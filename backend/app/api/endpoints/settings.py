from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings, logger
from app.utils.cloudflare_bypass import cf_bypasser
import httpx
import time

router = APIRouter()


class ProxySettings(BaseModel):
    use_proxy: bool
    proxy_url: str = ""


@router.get("/proxy", response_model=ProxySettings)
async def get_proxy_settings():
    """获取当前代理设置"""
    return ProxySettings(
        use_proxy=settings.USE_PROXY,
        proxy_url=settings.PROXY_URL
    )


@router.put("/proxy", response_model=dict)
async def set_proxy_settings(settings_data: ProxySettings):
    """设置代理（运行时生效）"""
    old_use_proxy = settings.USE_PROXY
    old_proxy_url = settings.PROXY_URL
    
    settings.USE_PROXY = settings_data.use_proxy
    settings.PROXY_URL = settings_data.proxy_url
    
    success = await cf_bypasser.set_proxy(settings_data.use_proxy, settings_data.proxy_url)
    
    if success:
        logger.info(f"代理设置已更新: use_proxy={settings_data.use_proxy}, proxy_url={settings_data.proxy_url}")
        return {
            "success": True,
            "message": "代理设置已更新",
            "restart_required": old_use_proxy != settings_data.use_proxy
        }
    else:
        settings.USE_PROXY = old_use_proxy
        settings.PROXY_URL = old_proxy_url
        return {
            "success": False,
            "message": "更新代理设置失败"
        }


@router.get("/proxy/test", response_model=dict)
async def test_proxy():
    """测试代理是否生效"""
    result = {
        "success": False,
        "message": "",
        "proxy_enabled": settings.USE_PROXY,
        "proxy_url": settings.PROXY_URL,
        "latency_ms": 0,
        "can_access_internet": False,
        "can_access_target": False
    }

    if not settings.USE_PROXY or not settings.PROXY_URL:
        result["message"] = "代理未启用"
        return result

    proxy_url = settings.PROXY_URL
    test_urls = [
        "https://www.google.com/generate_204",
        "https://www.baidu.com",
    ]

    for test_url in test_urls:
        try:
            start_time = time.time()
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                response = await client.get(test_url, follow_redirects=True)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 204 or response.status_code == 200:
                result["success"] = True
                result["message"] = f"代理连接成功，延迟 {elapsed_ms}ms"
                result["latency_ms"] = elapsed_ms
                result["can_access_internet"] = True
                logger.info(f"代理测试成功: {proxy_url}, 延迟 {elapsed_ms}ms")
                break
        except httpx.ConnectError as e:
            result["message"] = f"无法连接代理服务器: {str(e)}"
            logger.warning(f"代理连接失败: {proxy_url}, 错误: {e}")
        except httpx.TimeoutException:
            result["message"] = "代理请求超时"
            logger.warning(f"代理请求超时: {proxy_url}")
        except Exception as e:
            result["message"] = f"代理测试异常: {str(e)}"
            logger.warning(f"代理测试异常: {proxy_url}, 错误: {e}")

    return result
