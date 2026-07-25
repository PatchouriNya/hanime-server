"""重新刮削指定番剧系列"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from app.services.scrape_service import ScrapeService
from app.models.scrape import ScrapeMode
from app.config import settings, logger


async def main():
    series_name = "告白…… (2026)"
    logger.info(f"开始重新刮削: {series_name}")

    service = ScrapeService()
    result = await service.scrape_series(
        series_name=series_name,
        scrape_mode=ScrapeMode.TV_SHOW,
        is_rename_file=settings.SCRAPE_RENAME_FILE,
        is_reorganize_directory=settings.SCRAPE_REORGANIZE_DIRECTORY
    )

    print(f"\n=== 刮削结果 ===")
    print(f"成功: {result.is_success}")
    print(f"错误: {result.error_message}")
    print(f"NFO 文件数: {len(result.nfo_files)}")
    print(f"图片文件数: {len(result.image_files)}")
    if result.image_files:
        print("\n=== 生成的图片文件 ===")
        for img in result.image_files:
            print(f"  {img}")


if __name__ == "__main__":
    asyncio.run(main())
