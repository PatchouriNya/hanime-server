from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

import uvicorn
import time

from app.api.routes import api_router
from app.config import settings, logger
from app.utils.cloudflare_bypass import cf_bypasser
from app.services.user_service import user_service
from app.utils.auth import init_users_db


def log_proxy_status():
    """记录代理状态"""
    if settings.USE_PROXY and settings.PROXY_URL:
        proxy_info = settings.PROXY_URL
        if "@" in proxy_info:
            parts = proxy_info.split("@")
            proxy_info = f"***@{parts[1]}"
        logger.info(f"代理服务已启用，代理地址: {proxy_info}")
    else:
        logger.info("代理服务未启用")

    if settings.USE_DOWNLOAD_PROXY:
        logger.info("下载视频代理服务已启用")
    else:
        logger.info("下载视频代理服务未启用")

    if settings.CLOUDFLARE_BYPASS_SERVICE_URL:
        logger.info(f"Cloudflare Bypass服务已启用，服务地址: {settings.CLOUDFLARE_BYPASS_SERVICE_URL}")
    else:
        logger.info("Cloudflare Bypass服务未启用")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的事件处理"""
    logger.info(f"启动 {settings.APP_NAME} 服务")

    log_proxy_status()

    await user_service.initialize()
    logger.info("用户数据库初始化完成")

    await init_users_db()
    logger.info("用户认证数据库初始化完成")

    yield

    # 应用关闭时清理资源
    logger.info("应用关闭，清理 CF Bypass 连接...")
    await cf_bypasser.close()
    # 尝试关闭 MySQL 连接池（如果已初始化）
    try:
        from app.services.mysql_user_service import mysql_user_service
        await mysql_user_service.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请替换为实际的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载下载目录
app.mount("/downloads", StaticFiles(directory=str(settings.DOWNLOAD_PATH)), name="downloads")


# 日志中间件
# 过滤高频轮询请求，避免日志噪音
_POLL_PATHS = {"/api/downloads/history", "/api/settings/version"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # 高频轮询请求只在非200时记录，减少日志噪音
    path = request.url.path
    if path in _POLL_PATHS and response.status_code == 200:
        return response
    logger.info(f"{request.method} {path} - {response.status_code} ({process_time:.2f}s)")
    return response


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"detail": "服务暂时不可用，请稍后重试"}
    )


# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "message": "欢迎使用HanimeViewer API",
        "version": settings.APP_VERSION,
        "status": "ok"
    }


# 处理所有未匹配的 /api/* 路由，返回标准 404 JSON 响应
# 避免前端收到 HTML 格式的 404 而触发"请求的资源不存在"错误提示
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_not_found(path: str):
    logger.warning(f"未匹配的 API 路由: /api/{path}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"API 端点 /api/{path} 不存在"}
    )


if __name__ == "__main__":
    # 配置日志拦截
    uvicorn.run(
        "main:app",  # 修改为直接引用当前文件中的app
        host=settings.HOST,  # 使用配置文件中的HOST设置
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False  # 禁用uvicorn的访问日志
    ) 