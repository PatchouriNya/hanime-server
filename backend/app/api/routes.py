from fastapi import APIRouter
from app.api.endpoints import videos, downloads, accounts, settings
from app.services.download_service import download_manager
from app.config import logger

api_router = APIRouter()

# 视频相关路由
api_router.include_router(
    videos.router,
    prefix="/videos",
    tags=["视频"]
)

# 下载相关路由
api_router.include_router(
    downloads.router,
    prefix="/downloads",
    tags=["下载"]
)

# 用户账户相关路由
api_router.include_router(
    accounts.router,
    prefix="/accounts/me",
    tags=["用户账户"]
)

# 设置相关路由
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["设置"]
)

@api_router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("应用关闭，清理连接池资源...")
    # 关闭所有HTTP客户端连接
    await download_manager.close_http_clients()
