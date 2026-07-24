"""端到端测试：删除已有 backdrop/landscape，重新生成，验证从视频截取"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')
from app.services.scrape_service import ScrapeService
from pathlib import Path


async def test():
    svc = ScrapeService()

    downloads_root = Path('/app/backend/data/downloads')
    # 找第一个有视频文件的番剧目录
    target_dir = None
    for d in sorted(downloads_root.iterdir()):
        if not d.is_dir():
            continue
        if svc._find_video_file(d):
            target_dir = d
            break

    if not target_dir:
        print('未找到含视频的番剧目录')
        return

    print(f'测试目录: {target_dir.name}')

    # 列出当前文件
    print('\n删除前的文件:')
    for f in sorted(target_dir.iterdir()):
        print(f'  {f.name}  ({f.stat().st_size} bytes)')

    # 删除 backdrop.jpg, landscape.jpg, fanart.jpg, thumb.jpg
    for name in ['backdrop.jpg', 'landscape.jpg', 'fanart.jpg',