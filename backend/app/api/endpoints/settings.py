from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings, logger, save_proxy_settings_to_file, save_download_dir_to_file
from app.utils.cloudflare_bypass import cf_bypasser
import httpx
import time
import re
from pathlib import Path

router = APIRouter()


class ProxySettings(BaseModel):
    use_proxy: bool
    proxy_url: str = ""


class DownloadDirSettings(BaseModel):
    download_path: str


class VersionInfo(BaseModel):
    """应用版本信息（v3.3.9: 已迁移到 routes.py 作为公开接口，无需登录）"""
    version: str
    app_name: str
    app_description: str


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
        save_proxy_settings_to_file()
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


@router.get("/download-dir")
async def get_download_dir():
    """获取当前下载目录"""
    return {"download_path": str(settings.DOWNLOAD_PATH)}


def _is_absolute_path(path_str: str) -> bool:
    """判断是否为绝对路径，兼容 Windows 和 Linux 格式"""
    # Linux/Mac: 以 / 开头
    if path_str.startswith('/'):
        return True
    # Windows: 以盘符开头，如 C:\ 或 D:/
    if re.match(r'^[a-zA-Z]:[/\\]', path_str):
        return True
    return False


@router.put("/download-dir")
async def set_download_dir(data: DownloadDirSettings):
    """设置下载目录，支持绝对路径（兼容 Windows 和 Linux 格式）"""
    path_str = data.download_path.strip().rstrip('/\\')
    try:
        if not _is_absolute_path(path_str):
            return {"success": False, "message": "请输入绝对路径，Linux: /app/downloads，Windows: D:\\Downloads"}

        new_path = Path(path_str)

        # 检测 Windows 路径在 Linux 环境下不可用
        import platform
        is_windows_path = bool(re.match(r'^[a-zA-Z]:[/\\]', path_str))
        if platform.system() != "Windows" and is_windows_path:
            return {
                "success": False,
                "message": "当前运行在 Linux/Docker 环境，不支持 Windows 路径。请使用 Linux 格式路径，如 /app/downloads，并确保目录已挂载"
            }

        new_path.mkdir(parents=True, exist_ok=True)

        old_path = settings.DOWNLOAD_PATH
        settings.DOWNLOAD_PATH = new_path
        settings.COVER_PATH = new_path / "covers"
        # 持久化下载目录设置，重启后自动恢复
        save_download_dir_to_file()
        logger.info(f"下载目录已更新: {old_path} -> {new_path}")
        return {"success": True, "message": "下载目录已更新", "download_path": str(new_path)}
    except PermissionError:
        logger.error(f"没有权限创建目录: {new_path}")
        return {"success": False, "message": f"没有权限创建目录: {new_path}"}
    except Exception as e:
        logger.error(f"设置下载目录失败: {str(e)}")
        return {"success": False, "message": f"设置下载目录失败: {str(e)}"}


@router.post("/open-dir")
async def open_download_dir():
    """打开下载目录（Docker/headless环境中仅返回路径）"""
    import subprocess
    import platform
    import shutil

    dir_path = str(settings.DOWNLOAD_PATH)

    # 检测是否有可用的文件管理器
    system = platform.system()
    opener = None
    if system == "Windows":
        opener = "explorer"
    elif system == "Darwin":
        opener = "open"
    elif shutil.which("xdg-open"):
        opener = "xdg-open"

    if opener:
        try:
            subprocess.Popen([opener, dir_path])
            return {"success": True, "message": f"已打开目录: {dir_path}", "path": dir_path}
        except Exception as e:
            logger.warning(f"打开目录失败: {str(e)}")

    # 无文件管理器可用（如Docker环境），返回路径信息
    return {
        "success": False,
        "message": f"当前环境无法打开文件管理器，请手动访问: {dir_path}",
        "path": dir_path
    }


@router.post("/clear-cache/home")
async def clear_home_cache():
    """清除首页数据缓存，用于刷新推荐内容"""
    from app.api.endpoints.videos import get_home_page
    get_home_page.cache_clear()
    logger.info("首页缓存已清除")
    return {"success": True, "message": "首页缓存已清除"}
