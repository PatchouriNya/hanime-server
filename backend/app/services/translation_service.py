"""翻译服务

v3.3.9 新增：刮削时自动翻译简介/描述到目标语言

使用多个 Google Translate 公开端点轮询尝试（无需 API key）：
1. https://translate.googleapis.com/translate_a/single?client=gtx
2. https://clients5.google.com/translate_a/t?client=dict-chrome-ex
3. https://translate.google.com/translate_a/single?client=at

参数：client=gtx (gtx 表示非官方客户端), sl=auto (源语言自动检测),
       tl=目标语言代码, dt=t (返回翻译结果), q=待翻译文本

支持的目标语言：
- zh-CN: 简体中文（默认）
- ja: 日文
- en: 英文
- off: 不翻译（保留原文）

注意：
- 长文本会被截断到 4500 字符/段（Google 公开端点限制）
- 失败时返回原文，不影响刮削主流程
- 文本过长时会分段翻译后拼接
- 多端点轮询：第一个端点被限流（429）时自动切换下一个
"""
import asyncio
import hashlib
import time
from typing import Optional, Dict, Tuple

import httpx

from app.config import settings, logger
from app.utils.cloudflare_bypass import cf_bypasser


# v4.0.0: 翻译结果缓存（内存 LRU）
# 批量刮削时同一段简介会在多个系列间重复出现，缓存避免对 Google 端点重复请求
_TRANSLATION_CACHE_MAX_ITEMS = 2000
_TRANSLATION_CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 天
_translation_cache: Dict[str, Tuple[float, str]] = {}


def _translation_cache_key(target_lang: str, text: str) -> str:
    """缓存键：目标语言 + 文本 MD5（避免超长 key）"""
    return f"{target_lang}:{hashlib.md5(text.encode('utf-8')).hexdigest()}"


def _translation_cache_get(target_lang: str, text: str) -> Optional[str]:
    key = _translation_cache_key(target_lang, text)
    cached = _translation_cache.get(key)
    if cached and time.time() - cached[0] < _TRANSLATION_CACHE_TTL_SECONDS:
        return cached[1]
    return None


def _translation_cache_set(target_lang: str, text: str, translated: str) -> None:
    key = _translation_cache_key(target_lang, text)
    _translation_cache[key] = (time.time(), translated)
    if len(_translation_cache) > _TRANSLATION_CACHE_MAX_ITEMS:
        now = time.time()
        expired = [k for k, (ts, _) in _translation_cache.items()
                   if now - ts >= _TRANSLATION_CACHE_TTL_SECONDS]
        for k in expired:
            del _translation_cache[k]
        if len(_translation_cache) > _TRANSLATION_CACHE_MAX_ITEMS:
            for k in list(_translation_cache)[:len(_translation_cache) - _TRANSLATION_CACHE_MAX_ITEMS]:
                del _translation_cache[k]


# 多个 Google Translate 公开端点（按优先级排序）
GOOGLE_TRANSLATE_ENDPOINTS = [
    "https://translate.googleapis.com/translate_a/single",
    "https://clients5.google.com/translate_a/t",
    "https://translate.google.com/translate_a/single",
]

# 单次翻译最大字符数（Google 公开端点限制）
MAX_TEXT_LENGTH_PER_REQUEST = 4500

# 支持的目标语言代码
SUPPORTED_LANGS = {"zh-CN", "ja", "en", "off"}

# 429 限流后等待时间（秒）
RATE_LIMIT_WAIT = 2.0


class TranslationService:
    """简介翻译服务"""

    def __init__(self):
        # 复用 cf_bypasser 的 HTTP 客户端（已配置代理）
        self._client: Optional[httpx.AsyncClient] = None
        # 缓存当前可用的端点索引（避免每次都从第一个开始重试）
        self._endpoint_idx: int = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（复用 cf_bypasser 的代理设置）"""
        if self._client is None or self._client.is_closed:
            proxy = None
            if settings.USE_PROXY and settings.PROXY_URL:
                proxy = settings.PROXY_URL
            self._client = httpx.AsyncClient(
                proxy=proxy,
                timeout=20.0,
                follow_redirects=True,
                headers={
                    "User-Agent": settings.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @staticmethod
    def _split_text(text: str, max_length: int = MAX_TEXT_LENGTH_PER_REQUEST) -> list:
        """
        将长文本按段落切分，每段不超过 max_length 字符
        优先在段落边界切分，避免破坏句子
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        # 按换行符分段
        lines = text.split("\n")
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk = (current_chunk + "\n" + line) if current_chunk else line
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # 单行超过 max_length，按字符切分
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def _try_endpoint(
        self, client: httpx.AsyncClient, url: str, params: dict, text: str
    ) -> Optional[str]:
        """尝试单个端点，成功返回翻译文本，失败返回 None"""
        try:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.debug(f"翻译端点 {url} 失败: HTTP {response.status_code}")
                return None

            data = response.json()
            # Google Translate 返回格式：[[[翻译后文本, 原文, ...], ...], ...]
            if not data or not isinstance(data, list) or not data[0]:
                logger.debug(f"翻译端点 {url} 数据格式异常: {str(data)[:200]}")
                return None

            # 拼接所有翻译片段
            translated_parts = []
            for item in data[0]:
                if isinstance(item, list) and item[0]:
                    translated_parts.append(item[0])

            if not translated_parts:
                return None

            return "".join(translated_parts)

        except Exception as e:
            logger.debug(f"翻译端点 {url} 异常: {e}")
            return None

    async def translate_chunk(self, text: str, target_lang: str) -> str:
        """
        翻译单段文本（< 4500 字符）

        :param text: 待翻译文本
        :param target_lang: 目标语言代码（zh-CN/ja/en）
        :return: 翻译后的文本，失败时返回原文
        """
        if not text or not text.strip():
            return text

        if target_lang not in SUPPORTED_LANGS or target_lang == "off":
            return text

        # v4.0.0: 命中翻译缓存直接返回
        cached_result = _translation_cache_get(target_lang, text)
        if cached_result is not None:
            logger.debug(f"翻译缓存命中: 文本长度 {len(text)}, 目标 {target_lang}")
            return cached_result

        client = await self._get_client()
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }

        # 依次尝试所有端点（从上一次成功的位置开始）
        total_endpoints = len(GOOGLE_TRANSLATE_ENDPOINTS)
        for i in range(total_endpoints):
            idx = (self._endpoint_idx + i) % total_endpoints
            url = GOOGLE_TRANSLATE_ENDPOINTS[idx]

            # clients5 端点需要不同的 client 参数
            current_params = dict(params)
            if "clients5.google.com" in url:
                current_params["client"] = "dict-chrome-ex"
            elif "translate.google.com" in url:
                current_params["client"] = "at"

            result = await self._try_endpoint(client, url, current_params, text)
            if result is not None:
                # 缓存当前成功的端点
                self._endpoint_idx = idx
                # v4.0.0: 写入翻译缓存
                _translation_cache_set(target_lang, text, result)
                return result

            # 遇到 429 限流时，等待一段时间再尝试下一个端点
            await asyncio.sleep(RATE_LIMIT_WAIT)

        logger.warning(
            f"翻译失败（所有端点均失败，保留原文）: 文本长度 {len(text)} 字符, "
            f"目标语言 {target_lang}"
        )
        return text

    async def translate(self, text: str, target_lang: Optional[str] = None) -> str:
        """
        翻译文本到目标语言（主入口）

        :param text: 待翻译文本
        :param target_lang: 目标语言代码，None 则使用 settings.TRANSLATE_TARGET_LANG
        :return: 翻译后的文本；如果禁用翻译则返回原文
        """
        # 检查是否启用翻译
        if not settings.TRANSLATE_PLOT_ENABLED:
            return text

        if target_lang is None:
            target_lang = settings.TRANSLATE_TARGET_LANG

        # off 表示不翻译
        if target_lang == "off" or not target_lang:
            return text

        if not text or not text.strip():
            return text

        # 长文本分段翻译
        chunks = self._split_text(text)
        if len(chunks) == 1:
            return await self.translate_chunk(chunks[0], target_lang)

        # 并发翻译多个分段
        logger.info(f"翻译: 文本 {len(text)} 字符，分为 {len(chunks)} 段")
        tasks = [self.translate_chunk(chunk, target_lang) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        translated_parts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"第 {i+1} 段翻译失败（使用原文）: {result}")
                translated_parts.append(chunks[i])
            else:
                translated_parts.append(result)

        return "".join(translated_parts)


# 全局单例
translation_service = TranslationService()
