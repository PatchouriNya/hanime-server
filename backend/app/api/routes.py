from fastapi import APIRouter, Depends
from app.api.endpoints import videos, downloads, accounts, settings, auth
from app.services.download_service import download_manager
from app.config import logger
from app.utils.auth import get_current_user

api_router = APIRouter()

# 认证相关路由（不需要登录）
api_router.include_router(
    auth.router,
    tags=["认证"]
)

# 视频相关路由（需要登录）
api_router.include_router(
    videos.router,
    prefix="/videos",
    tags=["视频"],
    dependencies=[Depends(get_current_user)]
)

# 下载相关路由（需要登录）
api_router.include_router(
    downloads.router,
    prefix="/downloads",
    tags=["下载"],
    dependencies=[Depends(get_current_user)]
)

# 封面图片路由（不需要 Bearer header 认证，通过 ?token=xxx 查询参数认证）
api_router.include_router(
    downloads.cover_router,
    prefix="/downloads",
    tags=["下载"]
)

# 用户账户相关路由（需要登录）
api_router.include_router(
    accounts.router,
    prefix="/accounts/me",
    tags=["用户账户"],
    dependencies=[Depends(get_current_user)]
)

# 设置相关路由（需要登录）
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["设置"],
    dependencies=[Depends(get_current_user)]
)

@api_router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("应用关闭，清理连接池资源...")
    # 关闭所有HTTP客户端连接
    await download_manager.close_http_clients()
