from pydantic import BaseModel, model_validator
from typing import Optional
import json as _json
from loguru import logger
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

import sys

# 尝试从项目根目录和当前目录加载环境变量
project_root = Path(__file__).parent.parent.parent  # 向上三级到项目根目录
backend_root = Path(__file__).parent.parent  # 向上两级到backend根目录
root_env_path = project_root / '.env'
local_env_path = backend_root / '.env'  # 后端目录下的.env

# 先尝试加载项目根目录的.env文件，然后尝试加载后端目录的.env文件
if root_env_path.exists():
    load_dotenv(dotenv_path=root_env_path)
    logger.info(f"从项目根目录加载.env文件: {root_env_path}")
elif local_env_path.exists():
    load_dotenv(dotenv_path=local_env_path)
    logger.info(f"从后端目录加载.env文件: {local_env_path}")
else:
    load_dotenv()  # 尝试默认加载
    logger.info("使用默认方式加载环境变量")


class Settings(BaseModel):
    # 基础设置
    APP_NAME: str = os.getenv("APP_NAME", "HanimeViewer")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "HanimeViewer API服务")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.4.1")
    RELOAD: bool = os.getenv("RELOAD", "False").lower() in ("true", "1", "t")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # 外部API设置
    HANIME_BASE_URL: str = os.getenv("HANIME_BASE_URL", "https://hanime1.me")

    # 数据根目录 - 所有用户数据统一存放于此，Docker 挂载这一个目录即可持久化
    DATA_ROOT: Path = Path(os.getenv("DATA_ROOT", str(backend_root / "data")))

    # 文件设置（默认值在 model_validator 中基于 DATA_ROOT 计算）
    DOWNLOAD_PATH: Path = Path(os.getenv("DOWNLOAD_PATH", ""))
    DB_PATH: Path = Path(os.getenv("DB_PATH", ""))
    COVER_PATH: Path = Path(os.getenv("COVER_PATH", ""))

    @model_validator(mode='after')
    def set_default_paths(self):
        """未通过环境变量指定路径时，使用 DATA_ROOT 下的默认路径"""
        if not os.getenv("DOWNLOAD_PATH"):
            self.DOWNLOAD_PATH = self.DATA_ROOT / "downloads"
        if not os.getenv("DB_PATH"):
            self.DB_PATH = self.DATA_ROOT / "db"
        if not os.getenv("COVER_PATH"):
            self.COVER_PATH = self.DATA_ROOT / "downloads" / "covers"
        return self

    # 爬虫设置
    USER_AGENT: str = os.getenv("USER_AGENT","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # 代理设置
    USE_PROXY: bool = os.getenv("USE_PROXY", "False").lower() in ("true", "1", "t")
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL")

    # 视频下载专用代理设置
    USE_DOWNLOAD_PROXY: bool = os.getenv("USE_DOWNLOAD_PROXY", "False").lower() in ("true", "1", "t")
    DOWNLOAD_PROXY_URL: Optional[str] = os.getenv("DOWNLOAD_PROXY_URL", os.getenv("PROXY_URL"))

    CLOUDFLARE_BYPASS_SERVICE_URL: str = os.getenv("CLOUDFLARE_BYPASS_SERVICE_URL", "")

    # 日志设置
    LOG_PATH: Path = Path(os.getenv("LOG_PATH", str(backend_root / "logs")))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    USE_LOG_FILE: bool = os.getenv("USE_LOG_FILE", "False").lower() in ("true", "1", "t")


settings = Settings()

# 代理配置验证：当USE_PROXY=true但PROXY_URL为空时，自动禁用代理
if settings.USE_PROXY and not settings.PROXY_URL:
    logger.warning("USE_PROXY=true 但 PROXY_URL 未配置，自动禁用代理")
    settings.USE_PROXY = False

if settings.USE_DOWNLOAD_PROXY and not settings.DOWNLOAD_PROXY_URL:
    logger.warning("USE_DOWNLOAD_PROXY=true 但 DOWNLOAD_PROXY_URL 未配置，自动禁用下载代理")
    settings.USE_DOWNLOAD_PROXY = False

# 从持久化文件恢复代理设置（覆盖 .env 默认值）
_proxy_file = settings.DB_PATH / "proxy_settings.json"
if _proxy_file.exists():
    try:
        _data = _json.loads(_proxy_file.read_text(encoding="utf-8"))
        if _data.get("use_proxy") is not None:
            settings.USE_PROXY = bool(_data["use_proxy"])
        if _data.get("proxy_url") is not None:
            settings.PROXY_URL = _data["proxy_url"]
        logger.info(f"已从持久化文件恢复代理设置: USE_PROXY={settings.USE_PROXY}")
    except Exception as e:
        logger.warning(f"恢复代理设置失败: {e}")

# 打印下载目录信息
logger.info(f"数据根目录: {settings.DATA_ROOT}")
logger.info(f"下载目录: {settings.DOWNLOAD_PATH}")
logger.info(f"数据库目录: {settings.DB_PATH}")
logger.info(f"封面目录: {settings.COVER_PATH}")

# 自动迁移旧路径数据到新的 DATA_ROOT 结构
import shutil as _shutil
_old_paths = {
    "db": backend_root / "db",
    "downloads": backend_root / "downloads",
}
for _name, _old in _old_paths.items():
    _new = settings.DATA_ROOT / _name
    if _old.exists() and _old.is_dir() and not _new.exists():
        try:
            _new.parent.mkdir(parents=True, exist_ok=True)
            _shutil.move(str(_old), str(_new))
            logger.info(f"已迁移旧目录 {_old} -> {_new}")
        except Exception as e:
            logger.warning(f"迁移旧目录 {_old} -> {_new} 失败: {e}，将使用新路径")

# 确保目录存在
settings.DOWNLOAD_PATH.mkdir(exist_ok=True, parents=True)
settings.DB_PATH.mkdir(exist_ok=True, parents=True)
settings.COVER_PATH.mkdir(parents=True, exist_ok=True)


# 配置并初始化logger
logger.remove()  # 移除默认处理程序

# 基础处理程序配置
handlers = [
    {
        "sink": sys.stdout,
        "format": settings.LOG_FORMAT,
        "level": settings.LOG_LEVEL,
        "colorize": True,
    }
]

# 根据开关决定是否添加文件日志处理程序
if settings.USE_LOG_FILE:
    # 确保日志目录存在
    settings.LOG_PATH.mkdir(exist_ok=True)
    logger.info(f"日志目录: {settings.LOG_PATH}")
    handlers.append({
        "sink": str(settings.LOG_PATH / "app.log"),
        "format": settings.LOG_FORMAT,
        "level": settings.LOG_LEVEL,
        "rotation": "10 MB",
        "retention": "7 days",
        "compression": "zip",
        "enqueue": True,
    })

logger.configure(handlers=handlers)


# 配置uvicorn日志拦截
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的Loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者的帧
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# 拦截uvicorn的日志
logging.basicConfig(handlers=[InterceptHandler()], level=0)

# 替换所有使用标准库logging的模块的处理程序
for _log in ['uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi']:
    _logger = logging.getLogger(_log)
    _logger.handlers = [InterceptHandler()]


def save_proxy_settings_to_file():
    """将当前代理设置持久化到文件，重启后自动恢复"""
    try:
        _proxy_file = settings.DB_PATH / "proxy_settings.json"
        _proxy_file.parent.mkdir(parents=True, exist_ok=True)
        _proxy_file.write_text(_json.dumps({
            "use_proxy": settings.USE_PROXY,
            "proxy_url": settings.PROXY_URL or ""
        }, ensure_ascii=False), encoding="utf-8")
        logger.info(f"代理设置已持久化: USE_PROXY={settings.USE_PROXY}")
    except Exception as e:
        logger.error(f"持久化代理设置失败: {e}")
