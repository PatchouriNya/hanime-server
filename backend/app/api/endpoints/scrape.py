"""刮削API端点

提供NFO刮削相关接口，包括：
- 获取/更新刮削配置
- 手动刮削指定番剧
- 批量刮削
- 预览刮削效果
- 扫描可刮削的番剧列表
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.scrape import (
    ScrapeConfig, ScrapeMode, ScrapeRequest,
    BatchScrapeRequest, ScrapeResult, ScrapableSeries, NfoPreview
)
from app.services.scrape_service import scrape_service
from app.config import settings, logger
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/config", response_model=ScrapeConfig)
async def get_scrape_config():
    """获取刮削配置"""
    return ScrapeConfig(
        scrape_mode=ScrapeMode(settings.SCRAPE_MODE),
        is_auto_scrape=settings.AUTO_SCRAPE_AFTER_DOWNLOAD,
        is_rename_file=settings.SCRAPE_RENAME_FILE,
        is_reorganize_directory=settings.SCRAPE_REORGANIZE_DIRECTORY,
        is_convert_cover_to_jpg=settings.SCRAPE_CONVERT_COVER_JPG,
        is_generate_fanart=False,
        is_translate_plot_enabled=settings.TRANSLATE_PLOT_ENABLED,
        translate_target_lang=settings.TRANSLATE_TARGET_LANG
    )


@router.put("/config")
async def update_scrape_config(config: ScrapeConfig, user: dict = Depends(get_current_user)):
    """更新刮削配置（运行时生效）"""
    try:
        settings.SCRAPE_MODE = config.scrape_mode.value
        settings.AUTO_SCRAPE_AFTER_DOWNLOAD = config.is_auto_scrape
        settings.SCRAPE_RENAME_FILE = config.is_rename_file
        settings.SCRAPE_REORGANIZE_DIRECTORY = config.is_reorganize_directory
        settings.SCRAPE_CONVERT_COVER_JPG = config.is_convert_cover_to_jpg
        # v3.3.9: 翻译设置
        settings.TRANSLATE_PLOT_ENABLED = config.is_translate_plot_enabled
        settings.TRANSLATE_TARGET_LANG = config.translate_target_lang

        # 持久化到文件
        _save_scrape_settings_to_file(config)

        logger.info(f"刮削配置已更新: mode={config.scrape_mode.value}, "
                     f"auto={config.is_auto_scrape}, "
                     f"rename={config.is_rename_file}, "
                     f"reorganize={config.is_reorganize_directory}, "
                     f"convert_jpg={config.is_convert_cover_to_jpg}, "
                     f"translate_enabled={config.is_translate_plot_enabled}, "
                     f"translate_lang={config.translate_target_lang}")
        return {"status": "success", "message": "刮削配置已保存"}
    except Exception as e:
        logger.error(f"更新刮削配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/series", response_model=ScrapeResult)
async def scrape_series(request: ScrapeRequest, user: dict = Depends(get_current_user)):
    """
    手动刮削指定番剧系列

    - series_name: 番剧目录名
    - scrape_mode: 电视剧/电影模式
    - is_rename_file: 是否重命名文件
    - is_reorganize_directory: 是否重组目录
    """
    return await scrape_service.scrape_series(
        series_name=request.series_name,
        scrape_mode=request.scrape_mode,
        is_rename_file=request.is_rename_file,
        is_reorganize_directory=request.is_reorganize_directory
    )


@router.post("/batch", response_model=List[ScrapeResult])
async def batch_scrape(request: BatchScrapeRequest, user: dict = Depends(get_current_user)):
    """批量刮削多个番剧系列（空列表则刮削所有）"""
    return await scrape_service.scrape_all_series(
        series_names=request.series_names if request.series_names else None,
        scrape_mode=request.scrape_mode,
        is_rename_file=request.is_rename_file,
        is_reorganize_directory=request.is_reorganize_directory
    )


@router.get("/preview/{series_name}", response_model=NfoPreview)
async def preview_scrape(series_name: str, user: dict = Depends(get_current_user)):
    """
    预览刮削效果

    返回将要生成的NFO内容、文件重命名映射等，不实际执行
    """
    scrape_mode = ScrapeMode(settings.SCRAPE_MODE)
    return await scrape_service.preview_scrape(series_name, scrape_mode)


@router.get("/scan", response_model=List[ScrapableSeries])
async def scan_scrapable_series(user: dict = Depends(get_current_user)):
    """
    扫描下载目录，返回所有可刮削的番剧系列

    返回每个系列的目录名、视频数量、是否已有NFO等信息
    """
    return await scrape_service.scan_scrapable_series()


@router.post("/fix-nfo")
async def fix_nfo_empty_tags(user: dict = Depends(get_current_user)):
    """
    修复已有 NFO 文件中的空日期标签

    绿联影视中心将 <year/>、<premiered/> 等空标签解析为 1970-01-01，
    此接口扫描所有 NFO 文件并移除空标签。
    """
    return await scrape_service.fix_nfo_empty_tags()


def _save_scrape_settings_to_file(config: ScrapeConfig):
    """将刮削设置持久化到文件"""
    try:
        import json
        scrape_file = settings.DB_PATH / "scrape_settings.json"
        scrape_file.parent.mkdir(parents=True, exist_ok=True)
        scrape_file.write_text(json.dumps({
            "scrape_mode": config.scrape_mode.value,
            "is_auto_scrape": config.is_auto_scrape,
            "is_rename_file": config.is_rename_file,
            "is_reorganize_directory": config.is_reorganize_directory,
            "is_convert_cover_to_jpg": config.is_convert_cover_to_jpg,
            "is_translate_plot_enabled": config.is_translate_plot_enabled,
            "translate_target_lang": config.translate_target_lang,
        }, ensure_ascii=False), encoding="utf-8")
        logger.info("刮削设置已持久化")
    except Exception as e:
        logger.error(f"持久化刮削设置失败: {e}")
