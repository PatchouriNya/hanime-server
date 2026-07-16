from typing import Dict, Optional
import httpx
import time
from app.config import settings, logger

CF_CHALLENGE_MARKERS = [
    "Just a moment...",
    "challenges.cloudflare.com",
    "cf-browser-verification",
    "cf_chl_opt",
    "_cf_chl_tk",
]


class CloudflareChallengedException(Exception):
    pass


class CloudflareBypasser:
    """用于绕过Cloudflare保护的客户端

    支持两种模式（按优先级）：
    1. Bypass 模式：通过外部 cf-bypass 服务转发请求
    2. 直接模式：通过 httpx 代理直连

    当 Bypass 服务不可用时，自动降级到直接代理模式。
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._direct_client: Optional[httpx.AsyncClient] = None
        self._bypass_available: Optional[bool] = None
        
        if settings.USE_PROXY and settings.PROXY_URL:
            import os
            os.environ['HTTP_PROXY'] = settings.PROXY_URL
            os.environ['HTTPS_PROXY'] = settings.PROXY_URL
            logger.info(f"[CF] 已设置全局代理环境变量: {settings.PROXY_URL}")

    @property
    async def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    async def direct_client(self) -> httpx.AsyncClient:
        if self._direct_client is None or self._direct_client.is_closed:
            proxy = settings.PROXY_URL if settings.USE_PROXY else None
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"Windows\"",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }
            self._direct_client = httpx.AsyncClient(timeout=30.0, proxy=proxy, headers=headers)
        return self._direct_client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        if self._direct_client and not self._direct_client.is_closed:
            await self._direct_client.aclose()
            self._direct_client = None

    def _use_bypass(self) -> bool:
        if self._bypass_available is False:
            return False
        if not settings.CLOUDFLARE_BYPASS_SERVICE_URL:
            if self._bypass_available is None:
                if settings.USE_PROXY and settings.PROXY_URL:
                    logger.info("[CF] 未配置 CLOUDFLARE_BYPASS_SERVICE_URL，代理已启用，使用直接代理模式")
                else:
                    logger.warning("[CF] 未配置 CLOUDFLARE_BYPASS_SERVICE_URL，未启用代理，可能无法访问目标网站")
                self._bypass_available = False
            return False
        return True

    def _build_bypass_url(self, target_url: str) -> tuple[str, str]:
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        bypass_base = settings.CLOUDFLARE_BYPASS_SERVICE_URL.rstrip('/')
        path_query = target_url.replace(f"{parsed.scheme}://{parsed.netloc}", "")
        if not path_query.startswith('/'):
            path_query = '/' + path_query
        return f"{bypass_base}{path_query}", parsed.netloc

    def _build_headers(self, hostname: str, force_refresh: bool = False) -> dict:
        headers = {"x-hostname": hostname}
        if force_refresh:
            headers["x-bypass-cache"] = "true"
        if settings.USE_PROXY and settings.PROXY_URL:
            headers["x-proxy"] = settings.PROXY_URL
        return headers

    @staticmethod
    def _is_cf_challenge(content: str) -> bool:
        if not content or len(content) < 50:
            return False
        snippet = content[:5000]
        return any(marker in snippet for marker in CF_CHALLENGE_MARKERS)

    async def _direct_get_request(self, url: str, params: Optional[Dict] = None,
                                  max_retries: int = 3) -> str:
        client = await self.direct_client
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"[Direct] GET {url} (第{attempt}次请求)")
                start_time = time.time()
                response = await client.get(url, params=params)
                elapsed = time.time() - start_time
                logger.debug(f"[Direct] 响应 {response.status_code}, 耗时 {elapsed:.2f}s")
                if response.status_code >= 500:
                    logger.warning(f"[Direct] 响应 {response.status_code}, 将重试")
                    continue
                return response.text
            except httpx.TimeoutException:
                logger.warning(f"[Direct] 请求超时 (attempt {attempt}/{max_retries}), URL: {url}")
            except Exception as e:
                logger.error(f"[Direct] 请求异常 (attempt {attempt}/{max_retries}): {e}")
        logger.error(f"[Direct] 已达最大重试次数({max_retries})，请求失败: {url}")
        return ""

    async def _direct_post_request(self, url: str, data: Dict,
                                   headers: Optional[Dict] = None,
                                   max_retries: int = 3) -> Dict:
        client = await self.direct_client
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"[Direct] POST {url} (第{attempt}次请求)")
                start_time = time.time()
                response = await client.post(url, data=data, headers=headers)
                elapsed = time.time() - start_time
                logger.debug(f"[Direct] POST 响应 {response.status_code}, 耗时 {elapsed:.2f}s")
                if response.status_code >= 500:
                    logger.warning(f"[Direct] POST 响应 {response.status_code}, 将重试")
                    continue
                try:
                    return response.json()
                except Exception:
                    logger.warning(f"[Direct] POST 响应非 JSON: {response.text[:100]}...")
                    return {}
            except httpx.TimeoutException:
                logger.warning(f"[Direct] POST 超时 (attempt {attempt}/{max_retries}), URL: {url}")
            except Exception as e:
                logger.error(f"[Direct] POST 异常 (attempt {attempt}/{max_retries}): {e}")
        logger.error(f"[Direct] POST 已达最大重试次数({max_retries})，请求失败: {url}")
        return {}

    async def get_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> str:
        if not self._use_bypass():
            return await self._direct_get_request(url, params, max_retries)

        bypass_url, hostname = self._build_bypass_url(url)
        client = await self.client

        for attempt in range(1, max_retries + 1):
            try:
                force_refresh = attempt > 1
                headers = self._build_headers(hostname, force_refresh=force_refresh)
                logger.debug(f"[CF] GET {url} (第{attempt}次请求, 强制刷新={force_refresh})")
                start_time = time.time()
                response = await client.get(bypass_url, params=params, headers=headers)
                elapsed = time.time() - start_time
                logger.debug(f"[CF] 响应 {response.status_code}, 耗时 {elapsed:.2f}s")

                if response.status_code >= 500:
                    logger.warning(f"[CF] Bypass 服务返回 {response.status_code}, 将重试")
                    continue

                content = response.text
                if self._is_cf_challenge(content):
                    logger.warning(f"[CF] 检测到 CF 挑战页面, 将强制刷新 cookie 重试")
                    continue

                self._bypass_available = True
                return content

            except httpx.TimeoutException:
                logger.warning(f"[CF] 请求超时 (attempt {attempt}/{max_retries}), URL: {url}")
            except httpx.ConnectError as e:
                logger.warning(f"[CF] 连接 Bypass 服务失败: {e}，降级为直接代理模式")
                self._bypass_available = False
                await self.close()
                return await self._direct_get_request(url, params, max_retries)
            except Exception as e:
                logger.error(f"[CF] 请求异常 (attempt {attempt}/{max_retries}): {e}, URL: {url}")

        logger.error(f"[CF] 已达最大重试次数({max_retries})，请求失败: {url}")
        return ""

    async def post_request(self, url: str, data: Dict, headers: Optional[Dict] = None,
                           max_retries: int = 3) -> Dict:
        if not self._use_bypass():
            return await self._direct_post_request(url, data, headers, max_retries)

        bypass_url, hostname = self._build_bypass_url(url)
        client = await self.client

        for attempt in range(1, max_retries + 1):
            try:
                force_refresh = attempt > 1
                req_headers = self._build_headers(hostname, force_refresh=force_refresh)
                if headers:
                    req_headers.update(headers)

                logger.debug(f"[CF] POST {url} (attempt {attempt}/{max_retries})")
                start_time = time.time()
                response = await client.post(bypass_url, data=data, headers=req_headers)
                elapsed = time.time() - start_time
                logger.debug(f"[CF] POST 响应 {response.status_code}, 耗时 {elapsed:.2f}s")

                if response.status_code >= 500:
                    logger.warning(f"[CF] Bypass 服务返回 {response.status_code}, 将重试")
                    continue

                if self._is_cf_challenge(response.text):
                    logger.warning(f"[CF] POST 检测到 CF 挑战页面, 将强制刷新 cookie 重试")
                    continue

                self._bypass_available = True
                try:
                    return response.json()
                except Exception:
                    logger.warning(f"[CF] POST 响应非 JSON: {response.text[:100]}...")
                    return {}

            except httpx.TimeoutException:
                logger.warning(f"[CF] POST 超时 (attempt {attempt}/{max_retries}), URL: {url}")
            except httpx.ConnectError as e:
                logger.warning(f"[CF] 连接 Bypass 服务失败: {e}，降级为直接代理模式")
                self._bypass_available = False
                await self.close()
                return await self._direct_post_request(url, data, headers, max_retries)
            except Exception as e:
                logger.error(f"[CF] POST 异常 (attempt {attempt}/{max_retries}): {e}, URL: {url}")

        logger.error(f"[CF] POST 已达最大重试次数({max_retries})，请求失败: {url}")
        return {}

    async def set_proxy(self, use_proxy: bool, proxy_url: str) -> bool:
        """运行时设置代理"""
        try:
            import os
            
            if use_proxy and proxy_url:
                os.environ['HTTP_PROXY'] = proxy_url
                os.environ['HTTPS_PROXY'] = proxy_url
                logger.info(f"[CF] 已更新全局代理环境变量: {proxy_url}")
            else:
                os.environ.pop('HTTP_PROXY', None)
                os.environ.pop('HTTPS_PROXY', None)
                logger.info("[CF] 已移除全局代理环境变量")
            
            if self._direct_client is not None and not self._direct_client.is_closed:
                await self._direct_client.aclose()
                self._direct_client = None
                logger.info("[CF] 已关闭旧的 direct_client，下次请求将使用新代理")
            
            return True
        except Exception as e:
            logger.error(f"[CF] 设置代理失败: {e}")
            return False


cf_bypasser = CloudflareBypasser()
