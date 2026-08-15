"""NFO刮削核心服务

为下载的里番生成NFO元数据文件和JPG封面图片，
使绿联4800plus NAS影视中心能正确识别和显示影片信息。

遵循 LibraryDream 命名规范：
- 函数名 snake_case
- 常量 UPPER_SNAKE_CASE
- 类名 PascalCase
"""
import asyncio
import os
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from xml.dom import minidom

from app.config import settings, logger
from app.models.scrape import (
    ScrapeMode, ScrapeResult, ScrapableSeries, NfoPreview
)
from app.services.video_service import VideoService
from app.utils.cloudflare_bypass import cf_bypasser

# NFO XML 声明（对齐绿联NAS识别格式，使用小写 utf-8）
NFO_XML_DECLARATION = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'

# 成人内容分级（对齐参考格式"未来日记"的 TV-MA）
MPAA_ADULT_RATING = "TV-MA"

# 默认视频时长（分钟）- 里番每集通常20-30分钟
DEFAULT_RUNTIME_MINUTES = 24

# 季海报文件名前缀（season01-poster.jpg，对齐参考格式）
SEASON_POSTER_FILENAME_PATTERN = "season{:02d}-poster.jpg"

# 制片国家
DEFAULT_COUNTRY = "Japan"

# 剧集状态
SERIES_STATUS_CONTINUING = "Continuing"

# 默认评分
DEFAULT_RATING = "7.6"

# 绿联NAS影视中心支持的图片格式（仅JPG！PNG不被识别）
SUPPORTED_IMAGE_FORMAT = "jpg"

# 视频文件扩展名
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".wmv", ".flv", ".ts"}

# NFO文件名常量
TVSHOW_NFO_FILENAME = "tvshow.nfo"
MOVIE_NFO_FILENAME = "movie.nfo"
SEASON_NFO_FILENAME = "season.nfo"
SEASON_DIR_PREFIX = "Season "

# 图片文件名常量
POSTER_FILENAME = "poster.jpg"
BACKDROP_FILENAME = "backdrop.jpg"
FANART_FILENAME = "fanart.jpg"
LANDSCAPE_FILENAME = "landscape.jpg"
THUMB_FILENAME = "thumb.jpg"
BANNER_FILENAME = "banner.jpg"

# 标准图片尺寸（对齐绿联4800plus参考格式）
POSTER_STANDARD_WIDTH = 1000
POSTER_STANDARD_HEIGHT = 1426
BACKDROP_STANDARD_WIDTH = 1920
BACKDROP_STANDARD_HEIGHT = 1080
LANDSCAPE_STANDARD_WIDTH = 1000
LANDSCAPE_STANDARD_HEIGHT = 562
BANNER_STANDARD_WIDTH = 1000
BANNER_STANDARD_HEIGHT = 185

# 图片 URL 路径常量（hanime 源站）
COVER_URL_PATH = "/image/cover/"
THUMBNAIL_URL_PATH = "/image/thumbnail/"

# 需要 CDATA 包裹的标签
CDATA_TAGS = ["plot", "outline"]


class ScrapeService:
    """NFO刮削服务"""

    def __init__(self):
        self.video_service = VideoService()
        # v3.6.3: 自动刮削互斥锁——多个下载并发完成时，串行执行自动刮削，
        # 避免多个全量刮削任务同时写同一批 NFO/图片/目录产生竞态
        self._auto_scrape_lock = asyncio.Lock()

    # ==================== 主流程 ====================

    async def fix_nfo_empty_tags(self, series_name: str = None) -> dict:
        """
        修复已有 NFO 文件中的空日期标签

        绿联影视中心将 <year/>、<premiered/> 等空标签解析为 1970-01-01。
        此方法扫描 NFO 文件，移除所有空日期标签。

        :param series_name: 指定番剧目录名，为 None 则修复所有
        :return: 修复统计 {"total": N, "fixed": N}
        """
        total = 0
        fixed = 0

        download_path = settings.DOWNLOAD_PATH
        if series_name:
            scan_dirs = [download_path / series_name]
        else:
            scan_dirs = [d for d in download_path.iterdir() if d.is_dir()] if download_path.exists() else []

        for series_dir in scan_dirs:
            if not series_dir.exists():
                continue
            # 扫描所有 .nfo 文件（包括子目录中的 episode nfo）
            for nfo_path in series_dir.rglob("*.nfo"):
                try:
                    content = nfo_path.read_text(encoding="utf-8")
                    cleaned = self._EMPTY_DATE_TAG_RE.sub('', content)
                    if cleaned != content:
                        nfo_path.write_text(cleaned, encoding="utf-8")
                        fixed += 1
                        logger.info(f"修复空日期标签: {nfo_path}")
                    total += 1
                except Exception as e:
                    logger.warning(f"修复 NFO 失败: {nfo_path} - {e}")

        return {"total": total, "fixed": fixed}

    async def scrape_series(
        self,
        series_name: str,
        scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW,
        is_rename_file: bool = True,
        is_reorganize_directory: bool = True,
        force_regenerate_covers: bool = True
    ) -> ScrapeResult:
        """
        对一个番剧系列执行刮削

        流程：
        1. 扫描番剧目录获取所有视频文件
        2. 从文件名解析 video_id
        3. 从 VideoService 获取元数据
        4. 生成 NFO 文件和图片
        5. 可选：重命名文件和重组目录

        v3.6.3 新增：force_regenerate_covers 控制单集封面是否强制重新下载。
        - True（默认）：每次刮削都重新下载每集封面（手动/批量刮削保持此行为）
        - False：已有封面则复用，只补缺失项（自动刮削使用，避免每次下载完都重复拉取所有封面）
        """
        result = ScrapeResult(
            series_name=series_name,
            scrape_mode=scrape_mode
        )

        series_dir = settings.DOWNLOAD_PATH / series_name
        if not series_dir.exists() or not series_dir.is_dir():
            result.is_success = False
            result.error_message = f"番剧目录不存在: {series_name}"
            return result

        try:
            # 1. 扫描番剧目录
            video_entries = self._scan_series_directory(series_dir)
            if not video_entries:
                result.is_success = False
                result.error_message = f"番剧目录中没有视频文件: {series_name}"
                return result

            # 1.5 补充无效 video_id（从数据库查找）
            for entry in video_entries:
                vid = entry.get("video_id", "")
                if not vid or not vid.isdigit():
                    db_vid = await self._lookup_video_id_from_db(Path(entry["file_path"]))
                    if db_vid:
                        entry["video_id"] = db_vid
                        logger.info(f"从数据库补充 video_id: {entry['filename']} -> {db_vid}")

            # 2. 获取元数据
            metadata_list = await self._fetch_metadata(video_entries)

            # 3. 确定集号（v3.3.4: 传入元数据用于真实集号识别）
            episode_mapping = self._determine_episode_number(video_entries, metadata_list)

            # 4. 生成 NFO 和图片
            if scrape_mode == ScrapeMode.TV_SHOW:
                nfo_files, image_files = await self._generate_tv_show_files(
                    series_dir, series_name, video_entries,
                    metadata_list, episode_mapping,
                    force_regenerate_covers=force_regenerate_covers
                )
            else:
                nfo_files, image_files = await self._generate_movie_files(
                    series_dir, series_name, video_entries,
                    metadata_list
                )

            result.nfo_files = nfo_files
            result.image_files = image_files

            # 5. 可选：重命名和目录重组
            if is_rename_file or is_reorganize_directory:
                renamed, series_dir = await self._reorganize_files(
                    series_dir, series_name, video_entries,
                    episode_mapping, scrape_mode,
                    is_rename_file, is_reorganize_directory,
                    metadata_list=metadata_list
                )
                result.renamed_files = renamed
                # v3.6.3: _reorganize_files 可能已将目录重命名为 "番剧名 (年份)"，
                # 使用返回的新路径，后续封面迁移/清理才能正确操作实际目录

            # 6. 把根目录的 {video_id}.jpg 文件移到中央封面目录（COVER_PATH）
            # 这些文件是下载时保存的封面，会干扰绿联NAS的影视库识别
            # （绿联NAS可能把它们当作独立的视频文件，导致剧集被拆分为多个条目）
            # 移到 COVER_PATH（/downloads/covers/）后：
            # - 系列目录保持干净，只含标准命名的 NFO/图片和 Season 子目录
            # - 封面文件仍保留，供后续重新刮削使用
            # - COVER_PATH 是系列目录的兄弟目录，NAS 不会将其识别为剧集
            central_covers_dir = settings.COVER_PATH
            central_covers_dir.mkdir(parents=True, exist_ok=True)
            # 在中央封面目录放置 .nomedia 文件，防止 NAS 扫描该目录
            # （COVER_PATH 位于 DOWNLOAD_PATH 下，NAS 会将其视为一个系列目录）
            nomedia_path = central_covers_dir / ".nomedia"
            if not nomedia_path.exists():
                try:
                    nomedia_path.write_text("", encoding="utf-8")
                except Exception:
                    pass
            moved_count = 0
            for f in series_dir.iterdir():
                if f.is_file() and f.suffix.lower() == ".jpg":
                    # 文件名是纯数字（video_id.jpg），且不是 poster/backdrop 等标准图片
                    if re.match(r'^\d+$', f.stem) and f.stem not in ("poster", "backdrop", "fanart", "landscape", "thumb", "banner"):
                        try:
                            target = central_covers_dir / f.name
                            shutil.move(str(f), str(target))
                            moved_count += 1
                        except Exception as e:
                            logger.warning(f"移动 {f.name} 到 {central_covers_dir} 失败: {e}")
            if moved_count > 0:
                logger.info(f"已将 {moved_count} 个封面文件移到中央封面目录: {central_covers_dir}")

            # 7. 清理旧的 .covers/ 目录（v3.3.0 之前的版本会创建此目录）
            old_covers_dir = series_dir / ".covers"
            if old_covers_dir.exists() and old_covers_dir.is_dir():
                try:
                    # 把 .covers/ 里的封面也移到中央封面目录
                    for f in old_covers_dir.iterdir():
                        if f.is_file():
                            target = central_covers_dir / f.name
                            if not target.exists():
                                shutil.move(str(f), str(target))
                    old_covers_dir.rmdir()
                    logger.info(f"已清理旧的 .covers/ 目录: {old_covers_dir}")
                except Exception as e:
                    logger.warning(f"清理 .covers/ 目录失败: {e}")

            # 8. 清理空的残留目录（v3.3.4 新增）
            # 旧版本（v3.3.3 及之前）系列识别错误时，可能为同一系列创建多个目录
            # 例如："○○交配 第一話 ..." 和 "○○交配 第十一話 ... 前編" 是两个独立目录
            # 系列识别修复后，这些目录的视频会被移动到正确的目录，但是空目录残留
            # 这里清理：
            #   a) 整个 DOWNLOAD_PATH 下没有任何视频文件和有效内容（只有空 Season 子目录）的目录
            #   b) 仅包含 .nfo/.jpg 等附属文件但没有视频文件的目录（视频已被移走）
            cleaned_dirs = self._cleanup_empty_series_directories(series_dir)
            if cleaned_dirs:
                result.renamed_files.extend([f"清理空目录: {d}" for d in cleaned_dirs])

            logger.success(f"刮削完成: {series_name}, "
                           f"NFO {len(nfo_files)} 个, "
                           f"图片 {len(image_files)} 个, "
                           f"重命名 {len(result.renamed_files)} 个")
            return result

        except Exception as e:
            logger.error(f"刮削番剧 {series_name} 失败: {e}")
            result.is_success = False
            result.error_message = str(e)
            return result

    async def auto_scrape_after_download(self, video_id: str):
        """
        下载完成后自动刮削

        v3.6.3 对齐说明：此处对整系列执行全量刮削（简单可靠，且会补全缺失的 NFO），
        但传入 force_regenerate_covers=False，已有单集封面直接复用，只补缺失项，
        避免每下载一集都重新拉取整个系列的所有封面。
        同时通过 _auto_scrape_lock 串行化并发触发的自动刮削，防止竞态。
        """
        async with self._auto_scrape_lock:
            await self._auto_scrape_after_download_locked(video_id)

    async def _auto_scrape_after_download_locked(self, video_id: str):
        """自动刮削的实际逻辑（在互斥锁内执行）"""
        try:
            # 查找该 video_id 对应的下载记录
            # 优先从数据库获取文件路径，再在磁盘上查找
            download_info = None

            # 方法1：从数据库获取 filename
            try:
                import aiosqlite
                db_path = settings.DB_PATH / "downloads.db"
                async with aiosqlite.connect(db_path) as conn:
                    conn.row_factory = aiosqlite.Row
                    async with conn.execute(
                        "SELECT filename FROM downloads WHERE video_id = ? AND status = 'completed'",
                        (video_id,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            file_path = settings.DOWNLOAD_PATH / row['filename']
                            if file_path.exists():
                                series_dir = file_path.parent
                                # 如果文件在 Season 子目录中，系列目录是上一级
                                if series_dir.name.startswith('Season '):
                                    series_dir = series_dir.parent
                                download_info = {
                                    "series_dir": series_dir,
                                    "series_name": series_dir.name,
                                    "video_file": file_path,
                                    "video_id": video_id
                                }
            except Exception as db_err:
                logger.warning(f"自动刮削: 数据库查询失败: {db_err}")

            # 方法2：如果数据库没找到，在磁盘上递归搜索
            if not download_info:
                for series_dir in settings.DOWNLOAD_PATH.iterdir():
                    if not series_dir.is_dir():
                        continue
                    # 递归搜索所有子目录（包括 Season 子目录）
                    for video_file in series_dir.rglob("*"):
                        if not video_file.is_file():
                            continue
                        if video_file.suffix.lower() not in VIDEO_EXTENSIONS:
                            continue
                        # 检查文件名中是否包含 video_id
                        if video_id in video_file.stem:
                            download_info = {
                                "series_dir": series_dir,
                                "series_name": series_dir.name,
                                "video_file": video_file,
                                "video_id": video_id
                            }
                            break
                    if download_info:
                        break

            if not download_info:
                logger.warning(f"自动刮削: 未找到 video_id={video_id} 对应的文件")
                return

            series_name = download_info["series_name"]
            series_dir = download_info["series_dir"]

            logger.info(f"自动刮削开始: {series_name} / {video_id}")

            # 使用配置的模式
            scrape_mode = ScrapeMode(settings.SCRAPE_MODE)

            # 刮削整个系列（简单可靠，且会补全缺失的NFO）
            # v3.6.3: force_regenerate_covers=False —— 复用已有单集封面，只补缺失
            result = await self.scrape_series(
                series_name=series_name,
                scrape_mode=scrape_mode,
                is_rename_file=settings.SCRAPE_RENAME_FILE,
                is_reorganize_directory=settings.SCRAPE_REORGANIZE_DIRECTORY,
                force_regenerate_covers=False
            )

            if result.is_success:
                logger.success(f"自动刮削完成: {series_name}")
            else:
                logger.warning(f"自动刮削失败: {series_name} - {result.error_message}")

        except Exception as e:
            logger.error(f"自动刮削异常: {e}")

    async def scrape_all_series(
        self,
        series_names: Optional[List[str]] = None,
        scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW,
        is_rename_file: bool = True,
        is_reorganize_directory: bool = True
    ) -> List[ScrapeResult]:
        """
        批量刮削所有番剧目录

        v3.3.9 优化：
        - 扫描目录时递归查找 Season 子目录中的视频文件
        - 跳过没有视频文件的目录（covers 等）
        - 详细记录每个目录的处理结果，方便前端展示进度
        """
        if series_names is None or len(series_names) == 0:
            # 扫描所有番剧目录（递归检查 Season 子目录）
            series_names = []
            if not settings.DOWNLOAD_PATH.exists():
                logger.warning(f"下载目录不存在: {settings.DOWNLOAD_PATH}")
                return []
            for item in settings.DOWNLOAD_PATH.iterdir():
                if not item.is_dir():
                    continue
                # 跳过中央封面目录（包含 .nomedia 的目录）
                if (item / ".nomedia").exists():
                    continue
                # 递归查找视频文件（包括 Season 子目录）
                has_video = False
                try:
                    for f in item.rglob("*"):
                        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                            has_video = True
                            break
                except PermissionError:
                    continue
                if has_video:
                    series_names.append(item.name)
                else:
                    logger.info(f"批量刮削: 跳过无视频文件的目录: {item.name}")

        logger.info(f"批量刮削: 共 {len(series_names)} 个目录待处理")

        results: List[ScrapeResult] = []
        for idx, name in enumerate(series_names, start=1):
            logger.info(f"批量刮削 [{idx}/{len(series_names)}]: {name}")
            result = await self.scrape_series(
                series_name=name,
                scrape_mode=scrape_mode,
                is_rename_file=is_rename_file,
                is_reorganize_directory=is_reorganize_directory
            )
            results.append(result)

        return results

    # ==================== NFO 生成 ====================

    def generate_tvshow_nfo(
        self,
        series_title: str,
        metadata_list: List[Optional[Any]],
        video_id: str = ""
    ) -> str:
        """
        生成 tvshow.nfo（电视剧总信息）

        完全对齐绿联4800plus NAS影视中心的识别格式：
        - plot/outline 用 CDATA 包裹
        - 不包含 thumb/fanart 标签（图片文件直接放在目录里，绿联自动识别）
        """
        root = ET.Element("tvshow")

        # 描述（使用第一个有描述的视频）- 放在最前面，对齐参考格式
        plot_text = ""
        for meta in metadata_list:
            if meta and hasattr(meta, "description") and meta.description:
                plot_text = meta.description
                break
        plot_elem = ET.SubElement(root, "plot")
        plot_elem.text = self._sanitize_nfo_text(plot_text)

        # outline 同 plot
        outline_elem = ET.SubElement(root, "outline")
        outline_elem.text = self._sanitize_nfo_text(plot_text)

        # 锁定数据
        lockdata_elem = ET.SubElement(root, "lockdata")
        lockdata_elem.text = "false"

        # 添加时间
        dateadded_elem = ET.SubElement(root, "dateadded")
        dateadded_elem.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 标题
        title_text = self._sanitize_nfo_text(series_title)
        title_elem = ET.SubElement(root, "title")
        title_elem.text = title_text

        # 原始标题（参考格式中与 title 相同）
        originaltitle_elem = ET.SubElement(root, "originaltitle")
        originaltitle_elem.text = title_text

        # 评分（综合算法：好评率+好评数+播放量+评论数，合集取平均值）
        valid_ratings = []
        for meta in metadata_list:
            if meta and hasattr(meta, "like_rate") and meta.like_rate:
                try:
                    rate_str = str(meta.like_rate).replace("%", "").replace("％", "")
                    rate_pct = float(rate_str)
                    like_count = getattr(meta, "like_count", 0) or 0
                    view_count = getattr(meta, "view_count", 0) or 0
                    comment_count = getattr(meta, "comment_count", 0) or 0
                    ep_rating = VideoService.calculate_rating(rate_pct, like_count, view_count, comment_count)
                    valid_ratings.append(ep_rating)
                except (ValueError, TypeError):
                    pass
        if valid_ratings:
            avg_rating = sum(valid_ratings) / len(valid_ratings)
            rating_value = f"{avg_rating:.1f}"
        else:
            rating_value = DEFAULT_RATING
        rating_elem = ET.SubElement(root, "rating")
        rating_elem.text = rating_value

        # 年份和首播日期 - 取所有元数据中最早日期
        earliest_date = None
        latest_date = None
        for meta in metadata_list:
            if meta and hasattr(meta, "upload_date") and meta.upload_date:
                try:
                    if isinstance(meta.upload_date, (datetime, date)):
                        date_val = meta.upload_date
                    else:
                        date_str = str(meta.upload_date)[:10]
                        date_val = datetime.strptime(date_str, "%Y-%m-%d")
                    if earliest_date is None or date_val < earliest_date:
                        earliest_date = date_val
                    if latest_date is None or date_val > latest_date:
                        latest_date = date_val
                except (ValueError, TypeError):
                    pass

        # 年份（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if earliest_date:
            year_elem = ET.SubElement(root, "year")
            year_elem.text = str(earliest_date.year)

        # 排序标题（取前4个字符作为缩写，对齐参考格式：sorttitle 在 year 之后）
        sorttitle_elem = ET.SubElement(root, "sorttitle")
        sorttitle_elem.text = title_text[:4] if title_text else ""

        # 分级（成人内容固定为 TV-MA，对齐参考格式"未来日记"）
        mpaa_elem = ET.SubElement(root, "mpaa")
        mpaa_elem.text = MPAA_ADULT_RATING

        # 首播日期和发布日期（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if earliest_date:
            premiered_elem = ET.SubElement(root, "premiered")
            premiered_elem.text = earliest_date.strftime("%Y-%m-%d")
            releasedate_elem = ET.SubElement(root, "releasedate")
            releasedate_elem.text = earliest_date.strftime("%Y-%m-%d")

        # 结束日期（如果有最新日期且与首播日期不同）
        if latest_date and earliest_date and latest_date != earliest_date:
            enddate_elem = ET.SubElement(root, "enddate")
            enddate_elem.text = latest_date.strftime("%Y-%m-%d")

        # 时长（分钟，从元数据解析或使用默认值）
        runtime_minutes = self._extract_runtime_minutes(metadata_list)
        runtime_elem = ET.SubElement(root, "runtime")
        runtime_elem.text = str(runtime_minutes)

        # 制片国家
        country_elem = ET.SubElement(root, "country")
        country_elem.text = DEFAULT_COUNTRY

        # 类型标签（固定添加"动画"和"成人"，再加视频类型）
        genres_added: Set[str] = {"动画", "成人"}
        for fixed_genre in ["动画", "成人"]:
            genre_elem = ET.SubElement(root, "genre")
            genre_elem.text = fixed_genre

        # 视频类型标签
        for meta in metadata_list:
            if meta and hasattr(meta, "video_type") and meta.video_type:
                vt_name = meta.video_type.name if hasattr(meta.video_type, "name") else str(meta.video_type)
                if vt_name and vt_name not in genres_added:
                    genre_elem = ET.SubElement(root, "genre")
                    genre_elem.text = self._sanitize_nfo_text(vt_name)
                    genres_added.add(vt_name)

        # 制作公司（去重合并）
        studios_added: Set[str] = set()
        for meta in metadata_list:
            if meta and hasattr(meta, "studio") and meta.studio:
                studio_name = meta.studio.name if hasattr(meta.studio, "name") else str(meta.studio)
                if studio_name and studio_name not in studios_added:
                    studio_elem = ET.SubElement(root, "studio")
                    studio_elem.text = self._sanitize_nfo_text(studio_name)
                    studios_added.add(studio_name)

        # 唯一标识符（不添加 default 属性，对齐参考格式）
        if video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.text = video_id

        # episodeguide（参考格式中保留此字段，即使内容为简单 JSON）
        if video_id:
            episodeguide_elem = ET.SubElement(root, "episodeguide")
            episodeguide_elem.text = f'{{"hanime":"{video_id}"}}'

        # id（参考格式中保留 id 字段，使用 video_id）
        if video_id:
            id_elem = ET.SubElement(root, "id")
            id_elem.text = video_id

        # season 和 episode（参考格式中是 -1，表示电视剧总信息）
        season_elem = ET.SubElement(root, "season")
        season_elem.text = "-1"
        episode_elem = ET.SubElement(root, "episode")
        episode_elem.text = "-1"

        # 显示顺序（对齐参考格式）
        displayorder_elem = ET.SubElement(root, "displayorder")
        displayorder_elem.text = "aired"

        # 状态
        status_elem = ET.SubElement(root, "status")
        status_elem.text = SERIES_STATUS_CONTINUING

        # 注意：参考格式中没有 thumb 和 fanart 标签，
        # 图片文件直接放在目录里，绿联会自动识别

        return self._pretty_xml(root)

    def generate_season_nfo(
        self,
        series_title: str,
        metadata_list: List[Optional[Any]],
        video_id: str,
        season_number: int,
        total_seasons: int = 1
    ) -> str:
        """
        生成 season.nfo（季信息）

        完全对齐绿联4800plus NAS影视中心的识别格式

        v3.3.8 调整：当整个合集只有 1 季时，season.nfo 的 title 直接用番剧名
        （不再加"第 1 季"后缀），避免在 NAS 上显示冗余的"第1季"字样。
        只有 total_seasons >= 2 时才使用"第 N 季"格式。
        """
        root = ET.Element("season")

        # 描述（使用第一个有描述的视频）
        plot_text = ""
        for meta in metadata_list:
            if meta and hasattr(meta, "description") and meta.description:
                plot_text = meta.description
                break
        plot_elem = ET.SubElement(root, "plot")
        plot_elem.text = self._sanitize_nfo_text(plot_text)

        # outline 同 plot
        outline_elem = ET.SubElement(root, "outline")
        outline_elem.text = self._sanitize_nfo_text(plot_text)

        # 锁定数据
        lockdata_elem = ET.SubElement(root, "lockdata")
        lockdata_elem.text = "false"

        # 添加时间
        dateadded_elem = ET.SubElement(root, "dateadded")
        dateadded_elem.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 季标题
        # v3.3.8: 单季合集直接用番剧名（不加"第 1 季"），多季合集才用"第 N 季"
        # 合集层面由 tvshow.nfo 的 title 显示番剧名
        if total_seasons >= 2:
            season_title = f"第 {season_number} 季"
        else:
            season_title = series_title
        title_elem = ET.SubElement(root, "title")
        title_elem.text = self._sanitize_nfo_text(season_title)

        # 年份
        earliest_date = None
        for meta in metadata_list:
            if meta and hasattr(meta, "upload_date") and meta.upload_date:
                try:
                    if isinstance(meta.upload_date, (datetime, date)):
                        date_val = meta.upload_date
                    else:
                        date_str = str(meta.upload_date)[:10]
                        date_val = datetime.strptime(date_str, "%Y-%m-%d")
                    if earliest_date is None or date_val < earliest_date:
                        earliest_date = date_val
                except (ValueError, TypeError):
                    pass

        year_elem = ET.SubElement(root, "year")
        sorttitle_elem = ET.SubElement(root, "sorttitle")
        # v3.3.8: sorttitle 与 title 保持一致（单季用番剧名，多季用"第 N 季"）
        sorttitle_elem.text = self._sanitize_nfo_text(season_title)
        premiered_elem = ET.SubElement(root, "premiered")
        releasedate_elem = ET.SubElement(root, "releasedate")
        if earliest_date:
            year_elem.text = str(earliest_date.year)
            premiered_elem.text = earliest_date.strftime("%Y-%m-%d")
            releasedate_elem.text = earliest_date.strftime("%Y-%m-%d")

        # 唯一标识符 - 使用与 tvshow.nfo 相同的 series ID
        # 对齐"未来日记 (2011)"参考格式：
        #   tvshow.nfo:      <uniqueid type="tmdb">46671</uniqueid>
        #   Season 1/season.nfo: <uniqueid type="tvdb">249827</uniqueid>  ← 与 tvshow.nfo 同一个 series ID
        # 关键点：所有季的 season.nfo 都使用同一个 series ID（不是每季不同的 video_id），
        # 这样绿联NAS 才能通过 uniqueid 识别所有季属于同一个合集。
        # 之前的错误：每季使用不同的 video_id 作为 uniqueid，导致 NAS 把每季识别为独立剧集。
        if video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.text = video_id

        # 季号
        seasonnumber_elem = ET.SubElement(root, "seasonnumber")
        seasonnumber_elem.text = str(season_number)

        return self._pretty_xml(root)

    def generate_episode_nfo(
        self,
        video_detail: Optional[Any],
        season_number: int,
        episode_number: int,
        episode_title: Optional[str] = None,
        series_name: str = ""
    ) -> str:
        """
        生成单集 .nfo 文件

        完全对齐绿联4800plus NAS影视中心的识别格式：
        - plot 用 CDATA 包裹，outline 留空
        - 字段顺序：plot→outline→lockdata→dateadded→title→rating→year→sorttitle→runtime→uniqueid→episode→season→aired
        - 不包含 thumb 标签（缩略图文件与视频同名 .jpg，绿联自动识别）
        """
        root = ET.Element("episodedetails")

        # 描述（CDATA 包裹）
        plot_text = ""
        if video_detail and hasattr(video_detail, "description") and video_detail.description:
            plot_text = video_detail.description
        plot_elem = ET.SubElement(root, "plot")
        plot_elem.text = self._sanitize_nfo_text(plot_text)

        # outline 留空（参考格式：<outline />）
        outline_elem = ET.SubElement(root, "outline")

        # 锁定数据
        lockdata_elem = ET.SubElement(root, "lockdata")
        lockdata_elem.text = "false"

        # 添加时间
        dateadded_elem = ET.SubElement(root, "dateadded")
        dateadded_elem.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 标题（优先使用 subtitle，其次 episode_title，最后"第 N 集"）
        title_text = episode_title or f"第 {episode_number} 集"
        if video_detail and hasattr(video_detail, "subtitle") and video_detail.subtitle:
            title_text = video_detail.subtitle
        title_text = self._sanitize_nfo_text(title_text)
        title_elem = ET.SubElement(root, "title")
        title_elem.text = title_text

        # 评分（综合算法）
        rating_value = DEFAULT_RATING
        if video_detail and hasattr(video_detail, "like_rate") and video_detail.like_rate:
            try:
                rate_str = str(video_detail.like_rate).replace("%", "").replace("％", "")
                rate_pct = float(rate_str)
                like_count = getattr(video_detail, "like_count", 0) or 0
                view_count = getattr(video_detail, "view_count", 0) or 0
                comment_count = getattr(video_detail, "comment_count", 0) or 0
                ep_rating = VideoService.calculate_rating(rate_pct, like_count, view_count, comment_count)
                rating_value = f"{ep_rating:.1f}"
            except (ValueError, TypeError):
                pass
        rating_elem = ET.SubElement(root, "rating")
        rating_elem.text = rating_value

        # 年份（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, (datetime, date)):
                    ep_year = str(video_detail.upload_date.year)
                else:
                    ep_year = str(video_detail.upload_date)[:4]
                year_elem = ET.SubElement(root, "year")
                year_elem.text = ep_year
            except (ValueError, TypeError):
                pass

        # 排序标题
        sorttitle_elem = ET.SubElement(root, "sorttitle")
        sorttitle_elem.text = title_text

        # 时长（从 duration 解析或使用默认值）
        runtime_minutes = self._parse_duration_to_minutes(
            video_detail.duration if video_detail and hasattr(video_detail, "duration") else None
        )
        runtime_elem = ET.SubElement(root, "runtime")
        runtime_elem.text = str(runtime_minutes)

        # 唯一标识符（从 video_detail 获取 video_id）
        # 注意：不添加 default="true" 属性，对齐参考格式（未来日记 episode.nfo 无 default 属性）
        ep_video_id = ""
        if video_detail and hasattr(video_detail, "video_id") and video_detail.video_id:
            ep_video_id = video_detail.video_id
        if ep_video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.text = ep_video_id

        # 集号和季号（对齐参考格式：episode 在 season 之前）
        episode_elem = ET.SubElement(root, "episode")
        episode_elem.text = str(episode_number)
        season_elem = ET.SubElement(root, "season")
        season_elem.text = str(season_number)

        # 播出日期（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, (datetime, date)):
                    aired_str = video_detail.upload_date.strftime("%Y-%m-%d")
                else:
                    aired_str = str(video_detail.upload_date)[:10]
                aired_elem = ET.SubElement(root, "aired")
                aired_elem.text = aired_str
            except (ValueError, TypeError):
                pass

        # 注意：参考格式中没有 thumb 标签，
        # 缩略图文件与视频同名（.jpg），绿联自动识别

        return self._pretty_xml(root)

    def generate_movie_nfo(
        self,
        video_detail: Optional[Any],
        video_id: str = ""
    ) -> str:
        """
        生成 movie.nfo（电影模式）

        完全对齐绿联4800plus NAS影视中心的识别格式：
        - plot/outline 用 CDATA 包裹
        - 不包含 thumb/fanart 标签（图片文件直接放在目录里，绿联自动识别）
        """
        root = ET.Element("movie")

        # 描述
        plot_text = ""
        if video_detail and hasattr(video_detail, "description") and video_detail.description:
            plot_text = video_detail.description
        plot_elem = ET.SubElement(root, "plot")
        plot_elem.text = self._sanitize_nfo_text(plot_text)

        # outline 同 plot
        outline_elem = ET.SubElement(root, "outline")
        outline_elem.text = self._sanitize_nfo_text(plot_text)

        # 锁定数据
        lockdata_elem = ET.SubElement(root, "lockdata")
        lockdata_elem.text = "false"

        # 添加时间
        dateadded_elem = ET.SubElement(root, "dateadded")
        dateadded_elem.text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 标题
        title_text = ""
        if video_detail:
            if hasattr(video_detail, "title") and video_detail.title:
                title_text = video_detail.title
            if hasattr(video_detail, "subtitle") and video_detail.subtitle:
                title_text = f"{title_text} {video_detail.subtitle}" if title_text else video_detail.subtitle

        if not title_text:
            title_text = "Unknown"

        title_text = self._sanitize_nfo_text(title_text)
        title_elem = ET.SubElement(root, "title")
        title_elem.text = title_text

        originaltitle_elem = ET.SubElement(root, "originaltitle")
        originaltitle_elem.text = title_text

        # 评分（综合算法）
        rating_value = DEFAULT_RATING
        if video_detail and hasattr(video_detail, "like_rate") and video_detail.like_rate:
            try:
                rate_str = str(video_detail.like_rate).replace("%", "").replace("％", "")
                rate_pct = float(rate_str)
                like_count = getattr(video_detail, "like_count", 0) or 0
                view_count = getattr(video_detail, "view_count", 0) or 0
                comment_count = getattr(video_detail, "comment_count", 0) or 0
                ep_rating = VideoService.calculate_rating(rate_pct, like_count, view_count, comment_count)
                rating_value = f"{ep_rating:.1f}"
            except (ValueError, TypeError):
                pass
        rating_elem = ET.SubElement(root, "rating")
        rating_elem.text = rating_value

        # 年份（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, (datetime, date)):
                    movie_year = str(video_detail.upload_date.year)
                else:
                    movie_year = str(video_detail.upload_date)[:4]
                year_elem = ET.SubElement(root, "year")
                year_elem.text = movie_year
            except (ValueError, TypeError):
                pass

        # 排序标题（对齐参考格式：sorttitle 在 year 之后）
        sorttitle_elem = ET.SubElement(root, "sorttitle")
        sorttitle_elem.text = title_text[:4] if title_text else ""

        # 分级
        mpaa_elem = ET.SubElement(root, "mpaa")
        mpaa_elem.text = MPAA_ADULT_RATING

        # 首播日期和发布日期（仅在有日期时创建，避免空标签导致绿联显示 1970）
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, (datetime, date)):
                    date_val = video_detail.upload_date
                else:
                    date_str = str(video_detail.upload_date)[:10]
                    date_val = datetime.strptime(date_str, "%Y-%m-%d")
                premiered_elem = ET.SubElement(root, "premiered")
                premiered_elem.text = date_val.strftime("%Y-%m-%d")
                releasedate_elem = ET.SubElement(root, "releasedate")
                releasedate_elem.text = date_val.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # 时长（从 duration 解析或使用默认值）
        runtime_minutes = self._parse_duration_to_minutes(
            video_detail.duration if video_detail and hasattr(video_detail, "duration") else None
        )
        runtime_elem = ET.SubElement(root, "runtime")
        runtime_elem.text = str(runtime_minutes)

        # 国家
        country_elem = ET.SubElement(root, "country")
        country_elem.text = DEFAULT_COUNTRY

        # 类型
        for fixed_genre in ["动画", "成人"]:
            genre_elem = ET.SubElement(root, "genre")
            genre_elem.text = fixed_genre

        # 视频类型
        if video_detail and hasattr(video_detail, "video_type") and video_detail.video_type:
            vt_name = video_detail.video_type.name if hasattr(video_detail.video_type, "name") else str(video_detail.video_type)
            if vt_name and vt_name not in {"动画", "成人"}:
                genre_elem = ET.SubElement(root, "genre")
                genre_elem.text = self._sanitize_nfo_text(vt_name)

        # 制作公司
        if video_detail and hasattr(video_detail, "studio") and video_detail.studio:
            studio_name = video_detail.studio.name if hasattr(video_detail.studio, "name") else str(video_detail.studio)
            if studio_name:
                studio_elem = ET.SubElement(root, "studio")
                studio_elem.text = self._sanitize_nfo_text(studio_name)

        # 唯一标识符（不添加 default 属性，对齐参考格式）
        if video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.text = video_id

            # id（参考格式中保留 id 字段）
            id_elem = ET.SubElement(root, "id")
            id_elem.text = video_id

        # 注意：参考格式中没有 thumb 和 fanart 标签，
        # 图片文件直接放在目录里，绿联会自动识别

        return self._pretty_xml(root)

    # ==================== 图片处理 ====================

    @staticmethod
    def _get_horizontal_thumbnail_url(cover_url: str) -> str:
        """
        从 cover URL 推导横向缩略图 URL

        hanime 源站图片 URL 规律：
        - 竖版海报：/image/cover/{filename}.jpg (268x394)
        - 横版缩略图：/image/thumbnail/{filename}.jpg (1024x576)

        两者共享相同的文件名，只是路径段不同。
        如果 cover_url 已经是 thumbnail 格式，直接返回；
        如果是 cover 格式，替换路径段；
        其他情况返回原 URL。
        """
        if not cover_url:
            return ""
        if THUMBNAIL_URL_PATH in cover_url:
            return cover_url
        if COVER_URL_PATH in cover_url:
            return cover_url.replace(COVER_URL_PATH, THUMBNAIL_URL_PATH)
        return cover_url

    @staticmethod
    def _parse_duration_to_minutes(duration: Optional[str]) -> int:
        """
        将 duration 字符串解析为分钟数

        支持的格式：
        - "HH:MM:SS"（如 "01:23:45"）
        - "MM:SS"（如 "23:45"）
        - "123 min" / "123分钟" 等带单位的数字
        - 纯数字（视为分钟）

        解析失败或为空时返回 DEFAULT_RUNTIME_MINUTES。
        向上取整（保证显示时长不会比实际短）。
        """
        if not duration:
            return DEFAULT_RUNTIME_MINUTES

        text = str(duration).strip()
        if not text:
            return DEFAULT_RUNTIME_MINUTES

        # 格式1：HH:MM:SS 或 MM:SS
        time_match = re.match(r'^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$', text)
        if time_match:
            parts = [int(g) for g in time_match.groups() if g is not None]
            if len(parts) == 3:
                hours, minutes, seconds = parts
            else:
                hours = 0
                minutes, seconds = parts
            total_seconds = hours * 3600 + minutes * 60 + seconds
            # 向上取整到分钟
            return max(1, (total_seconds + 59) // 60)

        # 格式2：带单位的数字（如 "123 min", "45分钟"）
        unit_match = re.match(r'^(\d+(?:\.\d+)?)\s*(min|mins|minute|minutes|分钟|分)?$', text, re.IGNORECASE)
        if unit_match:
            try:
                value = float(unit_match.group(1))
                # 向上取整
                return max(1, int(value) if value == int(value) else int(value) + 1)
            except (ValueError, TypeError):
                pass

        # 格式3：纯数字字符串（视为分钟）
        if text.isdigit():
            try:
                return max(1, int(text))
            except (ValueError, TypeError):
                pass

        return DEFAULT_RUNTIME_MINUTES

    def _extract_runtime_minutes(self, metadata_list: List[Optional[Any]]) -> int:
        """
        从元数据列表中提取时长（分钟）

        优先使用第一个有效 duration 解析的分钟数，
        解析失败或为空时返回 DEFAULT_RUNTIME_MINUTES。
        """
        for meta in metadata_list:
            if meta and hasattr(meta, "duration") and meta.duration:
                minutes = self._parse_duration_to_minutes(meta.duration)
                if minutes > 0:
                    return minutes
        return DEFAULT_RUNTIME_MINUTES

    async def generate_poster(
        self,
        series_dir: Path,
        cover_url: str
    ) -> bool:
        """
        生成 poster.jpg（竖版封面海报）

        绿联影视中心通过 poster.jpg 识别封面。
        1. 优先使用已有 poster.jpg
        2. 否则从已有封面文件复制/转换
        3. 最后从 URL 下载（使用 cf_bypasser 绕过 Cloudflare）
        4. 下载后用 PIL 放大到标准尺寸（1000x1426）使用 LANCZOS 重采样
        """
        poster_path = series_dir / POSTER_FILENAME

        # 如果已有 poster.jpg，直接使用
        if poster_path.exists():
            logger.info(f"poster.jpg 已存在: {poster_path}")
            return True

        # 尝试从已有封面文件复制/转换
        existing_cover = self._find_existing_cover(series_dir)
        if existing_cover:
            try:
                if settings.SCRAPE_CONVERT_COVER_JPG and existing_cover.suffix.lower() != ".jpg":
                    success = self._convert_image_to_jpg(existing_cover, poster_path)
                    if success:
                        self._upscale_to_standard(poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT)
                        logger.info(f"封面转换成功: {existing_cover} -> {poster_path}")
                        return True
                else:
                    shutil.copy2(existing_cover, poster_path)
                    self._upscale_to_standard(poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT)
                    logger.info(f"封面复制成功: {existing_cover} -> {poster_path}")
                    return True
            except Exception as e:
                logger.warning(f"封面处理失败: {e}")

        # 从URL下载（使用 cf_bypasser 绕过 Cloudflare）
        if cover_url:
            try:
                success = await self._download_cover_as_jpg(cover_url, poster_path)
                if success:
                    # 放大到标准尺寸以提升显示效果
                    self._upscale_to_standard(poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT)
                    return True
            except Exception as e:
                logger.warning(f"封面下载失败: {e}")

        # 如果URL下载失败，但已有本地封面（即使分辨率低），也比没有好
        if not poster_path.exists() and existing_cover:
            try:
                if settings.SCRAPE_CONVERT_COVER_JPG and existing_cover.suffix.lower() != ".jpg":
                    self._convert_image_to_jpg(existing_cover, poster_path)
                else:
                    shutil.copy2(existing_cover, poster_path)
                self._upscale_to_standard(poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT)
                return True
            except Exception:
                pass

        return False

    def _find_video_file(self, series_dir: Path) -> Optional[Path]:
        """
        在番剧目录中查找第一个可用的视频文件

        扫描顺序：Season 子目录 → 根目录
        :return: 视频文件 Path，无则 None
        """
        # 优先扫描 Season 子目录
        for sub in series_dir.iterdir():
            if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                for f in sorted(sub.iterdir()):
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                        return f

        # 回退扫描根目录
        for f in sorted(series_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                return f

        return None

    async def _extract_frame_from_video(
        self,
        video_path: Path,
        output_path: Path,
        seek_pct: float = 0.5
    ) -> bool:
        """
        用 ffmpeg 从视频文件截取一帧画面

        :param video_path: 视频文件路径
        :param output_path: 输出 jpg 路径
        :param seek_pct: 截取位置百分比（0.0~1.0），例如 0.5 表示视频中间
        :return: 成功 True，失败 False
        """
        try:
            # 先用 ffprobe 获取视频时长（秒）
            probe = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await probe.communicate()
            duration_str = stdout.decode().strip() if stdout else ""

            try:
                duration = float(duration_str)
            except (ValueError, TypeError):
                logger.warning(f"无法解析视频时长: {duration_str}，默认使用 600 秒")
                duration = 600.0

            if duration <= 0:
                duration = 600.0

            # 计算截取时间点（避开片头片尾 10%）
            seek_seconds = max(duration * 0.1, min(duration * seek_pct, duration * 0.9))

            # 用 ffmpeg 截取一帧（-ss 在 -i 前更快，是关键帧定位）
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{seek_seconds:.2f}",
                "-i", str(video_path),
                "-frames:v", "1",
                "-q:v", "2",
                str(output_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            success = output_path.exists() and output_path.stat().st_size > 0
            if success:
                logger.info(f"从视频截取帧成功: {video_path.name} @ {seek_seconds:.1f}s -> {output_path.name}")
            else:
                logger.warning(f"从视频截取帧失败: {video_path.name}")
            return success

        except FileNotFoundError:
            logger.warning("ffmpeg/ffprobe 未安装，无法从视频截取帧")
            return False
        except Exception as e:
            logger.warning(f"从视频截取帧异常: {e}")
            return False

    async def generate_backdrop(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 backdrop.jpg（高分辨率横版背景图）

        策略（优先级从高到低）：
        1. 优先从已下载视频文件截取真实画面（随机时间点，避开片头片尾）
        2. 回退：从横向 thumbnail URL 下载（1024x576，源站原生横版）
        3. 回退：从 poster.jpg 裁剪 16:9 横条
        4. 回退：从 cover_url 下载并裁剪
        下载/截取后放大到 1920x1080 标准尺寸
        """
        backdrop_path = series_dir / BACKDROP_FILENAME

        if backdrop_path.exists():
            logger.info(f"backdrop.jpg 已存在: {backdrop_path}")
            return True

        # 优先：从已下载视频文件截取真实画面
        video_file = self._find_video_file(series_dir)
        if video_file:
            try:
                success = await self._extract_frame_from_video(
                    video_file, backdrop_path, seek_pct=0.5
                )
                if success:
                    # 调整到标准尺寸 1920x1080（裁剪+缩放）
                    self._resize_to_standard(
                        backdrop_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT
                    )
                    logger.info(f"backdrop.jpg 从视频截取: {backdrop_path}")
                    return True
            except Exception as e:
                logger.warning(f"backdrop 从视频截取失败: {e}")

        # 回退：从横向 thumbnail URL 下载高分辨率横版图
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                success = await self._download_cover_as_jpg(thumbnail_url, backdrop_path)
                if success:
                    # 放大到标准尺寸 1920x1080
                    self._upscale_to_standard(backdrop_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT)
                    logger.info(f"backdrop.jpg 从 thumbnail URL 下载: {backdrop_path}")
                    return True
            except Exception as e:
                logger.warning(f"backdrop 从 thumbnail 下载失败: {e}")

        # 回退：从 poster.jpg 裁剪
        poster_path = series_dir / POSTER_FILENAME
        if poster_path.exists():
            try:
                success = self._crop_landscape_from_poster(poster_path, backdrop_path)
                if success:
                    self._upscale_to_standard(backdrop_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT)
                    logger.info(f"backdrop.jpg 从 poster.jpg 裁剪: {backdrop_path}")
                    return True
            except Exception as e:
                logger.warning(f"生成backdrop失败: {e}")

        # 最后回退：从原 cover_url 下载并裁剪
        if cover_url:
            try:
                import tempfile
                tmp_path = Path(tempfile.mktemp(suffix=".jpg"))
                success = await self._download_cover_as_jpg(cover_url, tmp_path)
                if success:
                    landscape_success = self._crop_landscape_from_poster(tmp_path, backdrop_path)
                    if tmp_path.exists():
                        tmp_path.unlink()
                    if landscape_success:
                        self._upscale_to_standard(backdrop_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT)
                        logger.info(f"backdrop.jpg 从下载封面裁剪: {backdrop_path}")
                        return True
                    if tmp_path.exists():
                        shutil.copy2(tmp_path, backdrop_path)
                    return True
            except Exception as e:
                logger.warning(f"backdrop下载失败: {e}")

        return False

    async def generate_fanart(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 fanart.jpg（背景图，与 backdrop 相同）

        绿联NAS影视中心通过 fanart.jpg 识别背景图。
        优先复制 backdrop.jpg，没有则重新下载生成。
        """
        fanart_path = series_dir / FANART_FILENAME

        if fanart_path.exists():
            logger.info(f"fanart.jpg 已存在: {fanart_path}")
            return True

        # 优先复制 backdrop.jpg
        backdrop_path = series_dir / BACKDROP_FILENAME
        if backdrop_path.exists():
            try:
                shutil.copy2(backdrop_path, fanart_path)
                logger.info(f"fanart.jpg 从 backdrop.jpg 复制: {fanart_path}")
                return True
            except Exception as e:
                logger.warning(f"生成fanart失败: {e}")

        # 回退：从 thumbnail URL 下载
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                success = await self._download_cover_as_jpg(thumbnail_url, fanart_path)
                if success:
                    self._upscale_to_standard(fanart_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT)
                    logger.info(f"fanart.jpg 从 thumbnail URL 下载: {fanart_path}")
                    return True
            except Exception as e:
                logger.warning(f"fanart 下载失败: {e}")

        # 最后回退：从 poster.jpg 裁剪
        poster_path = series_dir / POSTER_FILENAME
        if poster_path.exists():
            try:
                success = self._crop_landscape_from_poster(poster_path, fanart_path)
                if success:
                    self._upscale_to_standard(fanart_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT)
                    logger.info(f"fanart.jpg 从 poster.jpg 裁剪: {fanart_path}")
                    return True
            except Exception as e:
                logger.warning(f"生成fanart失败: {e}")

        return False

    async def generate_landscape(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 landscape.jpg（横版缩略图，列表页用）

        绿联影视中心列表页使用此图做缩略图。
        优先从已下载视频截取真实画面（与 backdrop 不同的时间点），
        回退从 thumbnail URL 下载，再回退复制 backdrop.jpg，最后从 poster 裁剪。
        """
        landscape_path = series_dir / LANDSCAPE_FILENAME

        if landscape_path.exists():
            logger.info(f"landscape.jpg 已存在: {landscape_path}")
            return True

        # 优先：从已下载视频文件截取真实画面（取 70% 位置，与 backdrop 的 50% 不同）
        video_file = self._find_video_file(series_dir)
        if video_file:
            try:
                success = await self._extract_frame_from_video(
                    video_file, landscape_path, seek_pct=0.7
                )
                if success:
                    # 调整到标准尺寸 1000x562（裁剪+缩放）
                    self._resize_to_standard(
                        landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT
                    )
                    logger.info(f"landscape.jpg 从视频截取: {landscape_path}")
                    return True
            except Exception as e:
                logger.warning(f"landscape 从视频截取失败: {e}")

        # 回退：从 thumbnail URL 下载
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                success = await self._download_cover_as_jpg(thumbnail_url, landscape_path)
                if success:
                    # 调整到标准尺寸 1000x562
                    self._resize_to_standard(landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                    logger.info(f"landscape.jpg 从 thumbnail URL 下载: {landscape_path}")
                    return True
            except Exception as e:
                logger.warning(f"landscape 下载失败: {e}")

        # 回退：复制 backdrop.jpg
        backdrop_path = series_dir / BACKDROP_FILENAME
        if backdrop_path.exists():
            try:
                shutil.copy2(backdrop_path, landscape_path)
                self._resize_to_standard(landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                logger.info(f"landscape.jpg 从 backdrop.jpg 复制: {landscape_path}")
                return True
            except Exception as e:
                logger.warning(f"生成landscape失败: {e}")

        # 最后回退：从 poster.jpg 裁剪
        poster_path = series_dir / POSTER_FILENAME
        if poster_path.exists():
            try:
                success = self._crop_landscape_from_poster(poster_path, landscape_path)
                if success:
                    self._resize_to_standard(landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                    logger.info(f"landscape.jpg 从 poster.jpg 裁剪: {landscape_path}")
                    return True
            except Exception as e:
                logger.warning(f"生成landscape失败: {e}")

        return False

    async def generate_thumb(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 thumb.jpg（横版缩略图，与 landscape 相同）

        绿联NAS影视中心通过 thumb.jpg 识别缩略图。
        优先复制 landscape.jpg，回退复制 backdrop.jpg。
        """
        thumb_path = series_dir / THUMB_FILENAME

        if thumb_path.exists():
            logger.info(f"thumb.jpg 已存在: {thumb_path}")
            return True

        # 优先复制 landscape.jpg
        landscape_path = series_dir / LANDSCAPE_FILENAME
        if landscape_path.exists():
            try:
                shutil.copy2(landscape_path, thumb_path)
                logger.info(f"thumb.jpg 从 landscape.jpg 复制: {thumb_path}")
                return True
            except Exception as e:
                logger.warning(f"生成thumb失败: {e}")

        # 回退：复制 backdrop.jpg
        backdrop_path = series_dir / BACKDROP_FILENAME
        if backdrop_path.exists():
            try:
                shutil.copy2(backdrop_path, thumb_path)
                self._resize_to_standard(thumb_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                logger.info(f"thumb.jpg 从 backdrop.jpg 复制: {thumb_path}")
                return True
            except Exception as e:
                logger.warning(f"生成thumb失败: {e}")

        # 最后回退：从 thumbnail URL 下载
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                success = await self._download_cover_as_jpg(thumbnail_url, thumb_path)
                if success:
                    self._resize_to_standard(thumb_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                    logger.info(f"thumb.jpg 从 thumbnail URL 下载: {thumb_path}")
                    return True
            except Exception as e:
                logger.warning(f"thumb 下载失败: {e}")

        # 最后从 poster 裁剪
        poster_path = series_dir / POSTER_FILENAME
        if poster_path.exists():
            try:
                success = self._crop_landscape_from_poster(poster_path, thumb_path)
                if success:
                    self._resize_to_standard(thumb_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT)
                    logger.info(f"thumb.jpg 从 poster.jpg 裁剪: {thumb_path}")
                    return True
            except Exception as e:
                logger.warning(f"生成thumb失败: {e}")

        return False

    async def generate_banner(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 banner.jpg（横幅图，长宽比 5.4:1，如 1000x185）

        绿联NAS影视中心通过 banner.jpg 识别横幅。
        从横向图（backdrop/landscape/thumb）裁剪中部 5.4:1 横条。
        """
        banner_path = series_dir / BANNER_FILENAME

        if banner_path.exists():
            logger.info(f"banner.jpg 已存在: {banner_path}")
            return True

        # 优先从已有的横向图裁剪
        for src_name in [BACKDROP_FILENAME, LANDSCAPE_FILENAME, THUMB_FILENAME, FANART_FILENAME]:
            src_path = series_dir / src_name
            if src_path.exists():
                try:
                    success = self._crop_banner_from_landscape(src_path, banner_path)
                    if success:
                        logger.info(f"banner.jpg 从 {src_name} 裁剪: {banner_path}")
                        return True
                except Exception as e:
                    logger.warning(f"生成banner失败: {e}")

        # 回退：从 thumbnail URL 下载后裁剪
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                import tempfile
                tmp_path = Path(tempfile.mktemp(suffix=".jpg"))
                success = await self._download_cover_as_jpg(thumbnail_url, tmp_path)
                if success:
                    banner_success = self._crop_banner_from_landscape(tmp_path, banner_path)
                    if tmp_path.exists():
                        tmp_path.unlink()
                    if banner_success:
                        logger.info(f"banner.jpg 从下载 thumbnail 裁剪: {banner_path}")
                        return True
                    # 裁剪失败就直接用原图
                    if tmp_path.exists():
                        shutil.copy2(tmp_path, banner_path)
                    return True
            except Exception as e:
                logger.warning(f"banner 下载失败: {e}")

        # 最后回退：从 poster.jpg 裁剪（极少情况）
        poster_path = series_dir / POSTER_FILENAME
        if poster_path.exists():
            try:
                # 先裁剪 16:9 横版，再裁剪 5.4:1 banner
                tmp_landscape = series_dir / ".tmp_landscape_for_banner.jpg"
                success = self._crop_landscape_from_poster(poster_path, tmp_landscape)
                if success:
                    banner_success = self._crop_banner_from_landscape(tmp_landscape, banner_path)
                    if tmp_landscape.exists():
                        tmp_landscape.unlink()
                    if banner_success:
                        logger.info(f"banner.jpg 从 poster.jpg 裁剪: {banner_path}")
                        return True
            except Exception as e:
                logger.warning(f"生成banner失败: {e}")

        return False

    async def generate_episode_thumb(
        self,
        season_dir: Path,
        season_number: int,
        episode_number: int,
        cover_url: str = "",
        series_name: str = "",
        force_regenerate: bool = False
    ) -> bool:
        """
        生成单集封面图（v3.3.5 调整：优先使用每集自己的 cover_url 竖版海报）

        文件名格式：番剧名 - S01E01 - 第 1 集.jpg
        与视频文件同名（.jpg），绿联自动识别。

        v3.3.5 优先级（高→低）：
        1. 每集自己的 cover_url（竖版海报 268x394，放大到 1000x1426）
           - 保证每集封面各不相同
        2. thumbnail URL（横版高分辨率 1024x576）
           - cover_url 失败时回退
        3. 从视频文件截取真实画面（ffmpeg 50% 位置）
           - 最后兜底

        :param force_regenerate: True 时强制重新生成（删除现有 .jpg）
        """
        safe_name = self._sanitize_filename(series_name) if series_name else ""
        season_str = f"S{season_number:02d}"
        episode_str = f"E{episode_number:02d}"

        if safe_name:
            thumb_filename = f"{safe_name} - {season_str}{episode_str} - 第 {episode_number} 集.jpg"
        else:
            thumb_filename = f"{season_str}{episode_str}-thumb.jpg"
        thumb_path = season_dir / thumb_filename

        # 强制重生：删除现有文件
        if force_regenerate and thumb_path.exists():
            try:
                thumb_path.unlink()
                logger.info(f"强制重生单集封面，已删除旧文件: {thumb_path.name}")
            except Exception as e:
                logger.warning(f"删除旧 episode thumb 失败: {e}")

        if thumb_path.exists():
            return True

        # 1. 优先：每集自己的 cover_url（理想情况为竖版海报）
        # 这是该集独立的封面，保证每集封面各不相同
        if cover_url:
            try:
                success = await self._download_cover_as_jpg(cover_url, thumb_path)
                if success:
                    # 检测下载图的实际方向（源站可能返回横版 thumbnail 而非竖版海报）
                    if self._is_landscape_image(thumb_path):
                        # 横版图（说明 cover_url 实际是 thumbnail 预览图 1024x576）
                        # 放大到 1920x1080 标准横版尺寸，不要强行拉伸为竖版
                        self._upscale_to_standard(
                            thumb_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT
                        )
                        logger.info(f"单集封面从 cover URL 下载（横版 thumbnail）: {thumb_path.name}")
                    else:
                        # 竖版图（真海报 268x394），放大到标准海报 1000x1426
                        self._upscale_to_standard(
                            thumb_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT
                        )
                        logger.info(f"单集封面从 cover URL 下载（竖版海报）: {thumb_path.name}")
                    return True
            except Exception as e:
                logger.warning(f"单集封面从 cover URL 下载失败: {e}")

        # 2. 回退：使用 thumbnail URL（横版高分辨率）
        thumbnail_url = self._get_horizontal_thumbnail_url(cover_url)
        if thumbnail_url:
            try:
                success = await self._download_cover_as_jpg(thumbnail_url, thumb_path)
                if success:
                    # 放大到 1920x1080 标准尺寸
                    self._upscale_to_standard(
                        thumb_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT
                    )
                    logger.info(f"单集封面从 thumbnail URL 下载（横版）: {thumb_path.name}")
                    return True
            except Exception as e:
                logger.warning(f"单集封面从 thumbnail 下载失败: {e}")

        # 3. 最后回退：从同名视频文件截取真实画面
        video_base_name = thumb_filename[:-4]  # 去掉 ".jpg"
        for ext in VIDEO_EXTENSIONS:
            video_candidate = season_dir / f"{video_base_name}{ext}"
            if video_candidate.exists():
                try:
                    success = await self._extract_frame_from_video(
                        video_candidate, thumb_path, seek_pct=0.5
                    )
                    if success:
                        self._resize_to_standard(
                            thumb_path, BACKDROP_STANDARD_WIDTH, BACKDROP_STANDARD_HEIGHT
                        )
                        logger.info(f"单集封面从视频截取（兜底）: {thumb_path.name}")
                        return True
                except Exception as e:
                    logger.warning(f"单集封面从视频截取失败: {e}")
                break

        return False

    def _crop_landscape_from_poster(self, poster_path: Path, landscape_path: Path) -> bool:
        """
        从竖版海报裁剪出横版缩略图

        裁剪策略：取图片中部 16:9 区域
        如果原图已经是横版(宽>高)，直接复制
        """
        try:
            from PIL import Image

            with Image.open(poster_path) as img:
                width, height = img.size

                # 如果已经是横版，直接保存
                if width >= height:
                    rgb_img = img.convert("RGB") if img.mode != "RGB" else img
                    rgb_img.save(landscape_path, "JPEG", quality=100, subsampling=0)
                    return True

                # 竖版图：从中间裁剪 16:9 横条
                # 目标高度 = 宽度 * 9 / 16（16:9比例）
                target_height = int(width * 9 / 16)
                if target_height > height:
                    # 图太窄，按实际高度计算最大宽度
                    target_height = height
                    target_width = int(height * 16 / 9)
                    if target_width > width:
                        target_width = width
                    left = (width - target_width) // 2
                    box = (left, 0, left + target_width, target_height)
                else:
                    # 从中间取横条
                    top = (height - target_height) // 2
                    box = (0, top, width, top + target_height)

                cropped = img.crop(box)
                rgb_img = cropped.convert("RGB") if cropped.mode != "RGB" else cropped
                rgb_img.save(landscape_path, "JPEG", quality=100, subsampling=0)
                return True

        except ImportError:
            # Pillow不可用，直接复制
            shutil.copy2(poster_path, landscape_path)
            return True
        except Exception as e:
            logger.error(f"裁剪landscape失败: {e}")
            return False

    def _crop_banner_from_landscape(self, landscape_path: Path, banner_path: Path) -> bool:
        """
        从横版图裁剪出 banner（长宽比 5.4:1，如 1000x185）

        裁剪策略：从横版图中部取 5.4:1 横条
        """
        try:
            from PIL import Image

            with Image.open(landscape_path) as img:
                width, height = img.size

                # 目标高度 = 宽度 / 5.4 （5.4:1 比例）
                target_height = int(width / 5.4)
                if target_height > height:
                    # 图太矮，按实际高度计算
                    target_height = height
                # 从中间取横条
                top = (height - target_height) // 2
                box = (0, top, width, top + target_height)

                cropped = img.crop(box)
                # 调整到标准尺寸 1000x185
                resized = cropped.resize(
                    (BANNER_STANDARD_WIDTH, BANNER_STANDARD_HEIGHT),
                    Image.Resampling.LANCZOS
                )
                rgb_img = resized.convert("RGB") if resized.mode != "RGB" else resized
                rgb_img.save(banner_path, "JPEG", quality=100, subsampling=0)
                return True

        except ImportError:
            # Pillow不可用，直接复制
            shutil.copy2(landscape_path, banner_path)
            return True
        except Exception as e:
            logger.error(f"裁剪banner失败: {e}")
            return False

    def _upscale_to_standard(self, image_path: Path, target_width: int, target_height: int) -> bool:
        """
        将图片放大到标准尺寸（仅放大，不缩小）

        使用 LANCZOS 重采样算法保证画质。
        如果原图已经大于等于目标尺寸，不处理。
        如果原图比例与目标比例不一致，先裁剪再缩放。
        """
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size

                # 如果已经大于等于目标尺寸，不处理
                if width >= target_width and height >= target_height:
                    return True

                # 计算目标比例
                target_ratio = target_width / target_height
                current_ratio = width / height

                if abs(current_ratio - target_ratio) > 0.05:
                    # 比例不一致，先裁剪
                    if current_ratio > target_ratio:
                        # 原图更宽，裁剪左右
                        new_width = int(height * target_ratio)
                        left = (width - new_width) // 2
                        box = (left, 0, left + new_width, height)
                    else:
                        # 原图更高，裁剪上下
                        new_height = int(width / target_ratio)
                        top = (height - new_height) // 2
                        box = (0, top, width, top + new_height)
                    img = img.crop(box)

                # 放大到目标尺寸
                resized = img.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS
                )
                rgb_img = resized.convert("RGB") if resized.mode != "RGB" else resized
                rgb_img.save(image_path, "JPEG", quality=100, subsampling=0)
                return True

        except ImportError:
            logger.warning("Pillow未安装，无法放大图片")
            return False
        except Exception as e:
            logger.warning(f"放大图片失败: {e}")
            return False

    def _resize_to_standard(self, image_path: Path, target_width: int, target_height: int) -> bool:
        """
        将图片调整到标准尺寸（裁剪+缩放，比例不一致时先裁剪）

        与 _upscale_to_standard 不同，此方法会强制调整到目标尺寸，
        即使原图更大也会缩小。
        """
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size

                # 如果尺寸已经一致，不处理
                if width == target_width and height == target_height:
                    return True

                # 计算目标比例
                target_ratio = target_width / target_height
                current_ratio = width / height

                if abs(current_ratio - target_ratio) > 0.05:
                    # 比例不一致，先裁剪
                    if current_ratio > target_ratio:
                        # 原图更宽，裁剪左右
                        new_width = int(height * target_ratio)
                        left = (width - new_width) // 2
                        box = (left, 0, left + new_width, height)
                    else:
                        # 原图更高，裁剪上下
                        new_height = int(width / target_ratio)
                        top = (height - new_height) // 2
                        box = (0, top, width, top + new_height)
                    img = img.crop(box)

                # 缩放到目标尺寸
                resized = img.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS
                )
                rgb_img = resized.convert("RGB") if resized.mode != "RGB" else resized
                rgb_img.save(image_path, "JPEG", quality=100, subsampling=0)
                return True

        except ImportError:
            logger.warning("Pillow未安装，无法调整图片尺寸")
            return False
        except Exception as e:
            logger.warning(f"调整图片尺寸失败: {e}")
            return False

    # ==================== 文件重命名和目录重组 ====================

    async def _reorganize_files(
        self,
        series_dir: Path,
        series_name: str,
        video_entries: List[Dict],
        episode_mapping: Dict[str, Dict],
        scrape_mode: ScrapeMode,
        is_rename_file: bool,
        is_reorganize_directory: bool,
        metadata_list: List[Optional[Any]] = None
    ) -> Tuple[List[str], Path]:
        """
        重命名视频文件并重组目录结构

        电视剧模式：
          单季: 番剧名/Season 1/番剧名 - S01E01 - 第 1 集.mp4
          多季: 番剧名/Season 1/番剧名 - S01E01 - 第 1 集.mp4
                番剧名/Season 2/番剧名 - S02E01 - 第 1 集.mp4

        电影模式：
          原始: 番剧名/video_id_subtitle.mp4
          目标: 番剧名 (年份)/番剧名 (年份).mp4

        如果番剧目录名尚未包含年份，且能从元数据获取到年份，则重命名目录为 "番剧名 (年份)"。
        多季时文件保留在其所属的 Season 目录中。

        v3.6.3 修复：返回 (重命名列表, 重命名后的最终系列目录)。
        此前目录被加年份重命名后，调用方仍持有旧路径，导致后续清理/封面迁移
        对不存在的目录操作而抛 FileNotFoundError，整个刮削被误判为失败。
        """
        renamed_files = []

        # 从元数据获取年份
        year_str = ""
        if metadata_list:
            first_meta = next((m for m in metadata_list if m), None)
            if first_meta and hasattr(first_meta, "upload_date") and first_meta.upload_date:
                try:
                    if isinstance(first_meta.upload_date, (datetime, date)):
                        year_str = f" ({first_meta.upload_date.year})"
                    else:
                        year_str = f" ({str(first_meta.upload_date)[:4]})"
                except (ValueError, TypeError):
                    pass

        # 重命名番剧目录（添加年份，避免重复添加）
        if is_reorganize_directory and year_str:
            # 检查目录名是否已包含年份（如 "番剧名 (2011)"）
            if not re.search(r'\(\d{4}\)', series_dir.name):
                new_dir_name = f"{series_name}{year_str}"
                new_series_dir = series_dir.parent / new_dir_name
                if series_dir != new_series_dir and not new_series_dir.exists():
                    old_dir_str = str(series_dir)
                    new_dir_str = str(new_series_dir)
                    old_dir_name = series_dir.name
                    new_dir_name_clean = new_series_dir.name
                    try:
                        series_dir.rename(new_series_dir)
                        renamed_files.append(f"目录重命名: {series_dir.name} -> {new_series_dir.name}")
                        logger.info(f"番剧目录重命名: {series_dir.name} -> {new_series_dir.name}")
                        series_dir = new_series_dir
                        # 更新 video_entries 中的文件路径，避免后续重命名时找不到文件
                        for entry in video_entries:
                            if entry.get("file_path", "").startswith(old_dir_str):
                                entry["file_path"] = new_dir_str + entry["file_path"][len(old_dir_str):]
                        # 同步更新数据库中的 filename 字段
                        try:
                            import aiosqlite
                            db_path = settings.DB_PATH / "downloads.db"
                            async with aiosqlite.connect(db_path) as conn:
                                await conn.execute(
                                    "UPDATE downloads SET filename = REPLACE(filename, ?, ?) WHERE filename LIKE ?",
                                    (f"{old_dir_name}/", f"{new_dir_name_clean}/", f"{old_dir_name}/%")
                                )
                                await conn.commit()
                                logger.info(f"数据库记录已更新: 目录重命名 {old_dir_name} -> {new_dir_name_clean}")
                        except Exception as db_err:
                            logger.warning(f"更新数据库目录重命名记录失败: {db_err}")
                    except Exception as e:
                        logger.error(f"番剧目录重命名失败: {e}")

        if scrape_mode == ScrapeMode.TV_SHOW:
            # 文件名中的系列名不应包含年份后缀（年份已在目录名中）
            # 例如：目录名 "欢迎光临！水龙敬乐园 (2017)"，文件名应为 "欢迎光临！水龙敬乐园 - S01E01"
            series_name_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', series_name).strip()
            safe_series_name = self._sanitize_filename(series_name_no_year)

            for entry in video_entries:
                video_path = Path(entry["file_path"])
                video_id = entry["video_id"]
                mapping = episode_mapping.get(video_id)
                if not mapping:
                    continue

                season_number = mapping["season"]
                episode_num = mapping["episode"]

                # 确定目标 Season 目录
                if is_reorganize_directory:
                    season_dir = series_dir / f"{SEASON_DIR_PREFIX}{season_number}"
                    season_dir.mkdir(parents=True, exist_ok=True)
                else:
                    # 不重组目录时，保留在当前目录
                    season_dir = video_path.parent

                if is_rename_file:
                    # 新文件名格式：番剧名 - S01E01 - 第 1 集.mp4
                    season_str = f"S{season_number:02d}"
                    episode_str = f"E{episode_num:02d}"
                    new_filename = (
                        f"{safe_series_name} - {season_str}{episode_str} - "
                        f"第 {episode_num} 集{video_path.suffix.lower()}"
                    )
                else:
                    new_filename = video_path.name

                new_path = season_dir / new_filename

                if video_path.exists() and video_path != new_path:
                    try:
                        # 清理旧的同名 NFO 和 JPG 文件（重命名前先移除）
                        old_stem = video_path.stem
                        for ext in [".nfo", ".jpg", ".jpeg", ".png", ".webp"]:
                            old_aux = video_path.with_suffix(ext)
                            if old_aux.exists():
                                try:
                                    old_aux.unlink()
                                    logger.info(f"清理旧附属文件: {old_aux.name}")
                                except Exception:
                                    pass

                        # 移动文件
                        shutil.move(str(video_path), str(new_path))
                        try:
                            relative_path = new_path.relative_to(series_dir)
                        except ValueError:
                            relative_path = new_path.name
                        renamed_files.append(f"{video_path.name} -> {relative_path}")
                        logger.info(f"文件重命名: {video_path.name} -> {relative_path}")
                        # 同步更新数据库中的 filename 字段
                        try:
                            import aiosqlite
                            db_path = settings.DB_PATH / "downloads.db"
                            # 计算新的相对路径（相对于 DOWNLOAD_PATH）
                            new_relative = f"{series_dir.name}/{relative_path}"
                            async with aiosqlite.connect(db_path) as db_conn:
                                # 先尝试通过 video_id 更新
                                await db_conn.execute(
                                    "UPDATE downloads SET filename = ? WHERE video_id = ?",
                                    (new_relative, video_id)
                                )
                                await db_conn.commit()
                                logger.info(f"数据库文件路径已更新: video_id={video_id}, filename={new_relative}")
                        except Exception as db_err:
                            logger.warning(f"更新数据库文件重命名记录失败: {db_err}")
                    except Exception as e:
                        logger.error(f"文件重命名失败: {video_path} -> {new_path}: {e}")

        elif scrape_mode == ScrapeMode.MOVIE:
            # 电影模式：重命名为 番剧名 (年份).mp4
            for entry in video_entries:
                video_path = Path(entry["file_path"])
                video_id = entry.get("video_id", "")

                if is_rename_file:
                    safe_name = self._sanitize_filename(series_name)
                    new_filename = f"{safe_name}{year_str}{video_path.suffix.lower()}"
                else:
                    new_filename = video_path.name

                new_path = series_dir / new_filename

                if video_path.exists() and video_path != new_path:
                    try:
                        shutil.move(str(video_path), str(new_path))
                        renamed_files.append(f"{video_path.name} -> {new_filename}")
                        logger.info(f"电影文件重命名: {video_path.name} -> {new_filename}")
                        # 同步更新数据库中的 filename 字段
                        if video_id:
                            try:
                                import aiosqlite
                                db_path = settings.DB_PATH / "downloads.db"
                                new_relative = f"{series_dir.name}/{new_filename}"
                                async with aiosqlite.connect(db_path) as db_conn:
                                    await db_conn.execute(
                                        "UPDATE downloads SET filename = ? WHERE video_id = ?",
                                        (new_relative, video_id)
                                    )
                                    await db_conn.commit()
                                    logger.info(f"数据库文件路径已更新: video_id={video_id}, filename={new_relative}")
                            except Exception as db_err:
                                logger.warning(f"更新数据库文件重命名记录失败: {db_err}")
                    except Exception as e:
                        logger.error(f"电影文件重命名失败: {e}")

        return renamed_files, series_dir

    # ==================== 扫描和预览 ====================

    async def scan_scrapable_series(self) -> List[ScrapableSeries]:
        """扫描下载目录，返回所有可刮削的番剧系列"""
        series_list = []

        if not settings.DOWNLOAD_PATH.exists():
            return series_list

        for item in settings.DOWNLOAD_PATH.iterdir():
            if not item.is_dir():
                continue

            # 跳过 Season 子目录
            if item.name.startswith(SEASON_DIR_PREFIX):
                continue

            video_files = []
            has_nfo = False
            has_poster = False

            # 扫描根目录
            for f in item.iterdir():
                if f.is_file():
                    if f.suffix.lower() in VIDEO_EXTENSIONS:
                        video_files.append(f.name)
                    elif f.name in (TVSHOW_NFO_FILENAME, MOVIE_NFO_FILENAME):
                        has_nfo = True
                    elif f.name == "poster.jpg":
                        has_poster = True

            # 扫描 Season 子目录
            for sub in item.iterdir():
                if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                    for f in sub.iterdir():
                        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                            video_files.append(f"{sub.name}/{f.name}")

            if video_files:
                series_list.append(ScrapableSeries(
                    series_name=item.name,
                    video_count=len(video_files),
                    has_nfo=has_nfo,
                    has_poster=has_poster,
                    video_files=video_files
                ))

        # 按名称排序
        series_list.sort(key=lambda x: x.series_name)
        return series_list

    async def preview_scrape(
        self,
        series_name: str,
        scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW
    ) -> NfoPreview:
        """预览刮削效果（不实际执行）"""
        series_dir = settings.DOWNLOAD_PATH / series_name
        if not series_dir.exists():
            return NfoPreview(series_name=series_name, scrape_mode=scrape_mode)

        video_entries = self._scan_series_directory(series_dir)
        metadata_list = await self._fetch_metadata(video_entries)
        episode_mapping = self._determine_episode_number(video_entries, metadata_list)

        preview = NfoPreview(
            series_name=series_name,
            scrape_mode=scrape_mode,
            rename_mapping=[]
        )

        if scrape_mode == ScrapeMode.TV_SHOW:
            # 预览 tvshow.nfo
            first_video_id = video_entries[0]["video_id"] if video_entries else ""
            preview.tvshow_nfo = self.generate_tvshow_nfo(
                series_name, metadata_list, first_video_id
            )

            # 预览单集NFO
            safe_series_name = self._sanitize_filename(series_name)
            for entry in video_entries:
                video_id = entry["video_id"]
                mapping = episode_mapping.get(video_id)
                if not mapping:
                    continue
                season_number = mapping["season"]
                episode_num = mapping["episode"]
                meta = next((m for i, m in enumerate(metadata_list)
                              if video_entries[i]["video_id"] == video_id), None)
                episode_nfo = self.generate_episode_nfo(
                    meta, season_number, episode_num, series_name=series_name
                )
                season_str = f"S{season_number:02d}"
                episode_str = f"E{episode_num:02d}"
                episode_filename = (
                    f"{safe_series_name} - {season_str}{episode_str} - 第 {episode_num} 集"
                )
                nfo_filename = f"{episode_filename}.nfo"
                preview.episode_nfos.append({
                    "filename": nfo_filename,
                    "content": episode_nfo
                })

                # 重命名映射
                original_name = Path(entry["file_path"]).name
                new_name = f"{episode_filename}.mp4"
                if original_name != new_name:
                    preview.rename_mapping.append({
                        "original": original_name,
                        "new": f"Season {season_number}/{new_name}"
                    })
        else:
            # 预览 movie.nfo
            meta = metadata_list[0] if metadata_list else None
            video_id = video_entries[0]["video_id"] if video_entries else ""
            preview.movie_nfo = self.generate_movie_nfo(meta, video_id)

        return preview

    # ==================== 内部辅助方法 ====================

    async def _generate_tv_show_files(
        self,
        series_dir: Path,
        series_name: str,
        video_entries: List[Dict],
        metadata_list: List[Optional[Any]],
        episode_mapping: Dict[str, Dict],
        force_regenerate_covers: bool = True
    ) -> tuple:
        """
        生成电视剧模式的NFO和图片文件

        目录结构对齐绿联4800plus NAS影视中心识别格式：
        番剧名 (年份)/
        ├── tvshow.nfo
        ├── poster.jpg, backdrop.jpg, fanart.jpg, landscape.jpg, thumb.jpg, banner.jpg
        ├── season01-poster.jpg, season02-poster.jpg, ...
        ├── Season 1/
        │   ├── poster.jpg（复制根目录）
        │   ├── season.nfo
        │   ├── 番剧名 - S01E01 - 第 1 集.nfo
        │   ├── 番剧名 - S01E01 - 第 1 集.jpg
        │   └── ...
        └── Season 2/
            ├── poster.jpg（复制根目录）
            ├── season.nfo
            ├── 番剧名 - S02E01 - 第 1 集.nfo
            └── ...

        支持多季：为每个季目录生成 season.nfo 和季海报，
        单集 NFO 使用 episode_mapping 中的正确季/集号。
        """
        nfo_files = []
        image_files = []

        # 获取合集海报的 cover_url
        # v3.5.0: 默认使用最早上传的剧集海报，可设置改为首次下载的海报
        first_video_id = video_entries[0]["video_id"] if video_entries else ""
        first_cover_url = ""

        if settings.POSTER_USE_EARLIEST_EPISODE:
            # 按上传日期排序，取最早上传的剧集的 cover_url
            earliest_meta = None
            earliest_date = None
            for meta in metadata_list:
                if meta and hasattr(meta, "cover_url") and meta.cover_url:
                    ud = getattr(meta, "upload_date", None)
                    if ud:
                        date_str = ud.isoformat() if isinstance(ud, (datetime, date)) else str(ud)
                        if earliest_date is None or date_str < earliest_date:
                            earliest_date = date_str
                            earliest_meta = meta
            if earliest_meta:
                first_cover_url = earliest_meta.cover_url
                logger.info(f"合集海报使用最早上传的剧集 cover: {earliest_date}")
            else:
                # 没有上传日期，回退到第一个有效的
                for meta in metadata_list:
                    if meta and hasattr(meta, "cover_url") and meta.cover_url:
                        first_cover_url = meta.cover_url
                        break
        else:
            # 使用首次遇到的有效 cover_url（第一次下载的那集）
            for meta in metadata_list:
                if meta and hasattr(meta, "cover_url") and meta.cover_url:
                    first_cover_url = meta.cover_url
                    break

        # 1. 生成 tvshow.nfo
        # NFO 中的标题不应包含年份后缀（年份已在目录名中）
        series_name_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', series_name).strip()
        tvshow_nfo_content = self.generate_tvshow_nfo(
            series_name_no_year, metadata_list, first_video_id
        )
        tvshow_nfo_path = series_dir / TVSHOW_NFO_FILENAME
        await self._write_nfo_file(tvshow_nfo_path, tvshow_nfo_content)
        nfo_files.append(str(tvshow_nfo_path))

        # 2. 生成 poster.jpg（竖版海报，绿联识别用）
        poster_success = await self.generate_poster(series_dir, first_cover_url)
        if poster_success:
            image_files.append(str(series_dir / POSTER_FILENAME))

        # 3. 生成 backdrop.jpg（横版背景图，从 poster 裁剪或下载）
        backdrop_success = await self.generate_backdrop(series_dir, first_cover_url)
        if backdrop_success:
            image_files.append(str(series_dir / BACKDROP_FILENAME))

        # 4. 生成 fanart.jpg（复制 backdrop）
        fanart_success = await self.generate_fanart(series_dir, first_cover_url)
        if fanart_success:
            image_files.append(str(series_dir / FANART_FILENAME))

        # 5. 生成 landscape.jpg（复制 backdrop）
        landscape_success = await self.generate_landscape(series_dir, first_cover_url)
        if landscape_success:
            image_files.append(str(series_dir / LANDSCAPE_FILENAME))

        # 6. 生成 thumb.jpg（复制 landscape）
        thumb_success = await self.generate_thumb(series_dir, first_cover_url)
        if thumb_success:
            image_files.append(str(series_dir / THUMB_FILENAME))

        # 7. 生成 banner.jpg（复制 landscape）
        banner_success = await self.generate_banner(series_dir, first_cover_url)
        if banner_success:
            image_files.append(str(series_dir / BANNER_FILENAME))

        # 8. 收集所有季号（从 episode_mapping 和目录结构中获取）
        season_numbers = set()
        for entry in video_entries:
            season_numbers.add(entry.get("season_number", 1))
        # 也从 episode_mapping 中获取
        for mapping_val in episode_mapping.values():
            season_numbers.add(mapping_val["season"])
        if not season_numbers:
            season_numbers = {1}

        # 构建 video_id -> metadata 映射（避免索引错位）
        vid_to_meta: Dict[str, Any] = {}
        for idx, entry in enumerate(video_entries):
            if idx < len(metadata_list) and metadata_list[idx]:
                vid = entry.get("video_id", "")
                if vid:
                    vid_to_meta[vid] = metadata_list[idx]

        # 9. 为每个季生成 Season 目录、season.nfo、季海报
        # 文件名中的系列名不应包含年份后缀（年份已在目录名中）
        series_name_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', series_name).strip()
        safe_series_name = self._sanitize_filename(series_name_no_year)

        for season_number in sorted(season_numbers):
            # 创建 Season 目录（对齐参考格式，不带前导零）
            season_dir = series_dir / f"{SEASON_DIR_PREFIX}{season_number}"
            season_dir.mkdir(parents=True, exist_ok=True)

            # 生成 season.nfo
            # 收集该季的元数据用于 season.nfo
            season_metadata = []
            for entry in video_entries:
                video_id = entry["video_id"]
                mapping = episode_mapping.get(video_id)
                if mapping and mapping["season"] == season_number:
                    m = vid_to_meta.get(video_id)
                    if m:
                        season_metadata.append(m)
            if not season_metadata:
                season_metadata = metadata_list

            # 使用该季第一个 video_id 作为 season 标识
            season_video_id = ""
            for entry in video_entries:
                mapping = episode_mapping.get(entry["video_id"])
                if mapping and mapping["season"] == season_number:
                    season_video_id = entry["video_id"]
                    break

            season_nfo_content = self.generate_season_nfo(
                series_name_no_year, season_metadata, first_video_id, season_number,
                total_seasons=len(season_numbers)
            )
            season_nfo_path = season_dir / SEASON_NFO_FILENAME
            await self._write_nfo_file(season_nfo_path, season_nfo_content)
            nfo_files.append(str(season_nfo_path))

            # 为 Season 目录生成独立的 poster.jpg
            # 每集一季策略：每季使用该集视频自己的封面，而非根目录的统一海报
            season_poster_path = season_dir / POSTER_FILENAME
            if not season_poster_path.exists():
                # 优先使用该季视频对应的 {video_id}.jpg（下载时保存的封面）
                # 查找位置：根目录 → 中央封面目录（COVER_PATH，刮削后会被移到这里）
                season_cover_path = series_dir / f"{season_video_id}.jpg"
                if not season_cover_path.exists():
                    central_candidate = settings.COVER_PATH / f"{season_video_id}.jpg"
                    if central_candidate.exists():
                        season_cover_path = central_candidate
                if season_cover_path.exists():
                    try:
                        shutil.copy2(season_cover_path, season_poster_path)
                        # 放大到标准尺寸 1000x1426
                        self._upscale_to_standard(
                            season_poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT
                        )
                        image_files.append(str(season_poster_path))
                        logger.info(f"Season {season_number} poster.jpg 从 {season_video_id}.jpg 生成")
                    except Exception as e:
                        logger.warning(f"Season {season_number} poster.jpg 从 {season_video_id}.jpg 生成失败: {e}")

                # 如果 {video_id}.jpg 不存在，从该季视频的 cover_url 下载
                if not season_poster_path.exists() and season_metadata:
                    cover_url = ""
                    if hasattr(season_metadata[0], "cover_url") and season_metadata[0].cover_url:
                        cover_url = season_metadata[0].cover_url
                    if cover_url:
                        try:
                            success = await self._download_cover_as_jpg(cover_url, season_poster_path)
                            if success:
                                self._upscale_to_standard(
                                    season_poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT
                                )
                                image_files.append(str(season_poster_path))
                                logger.info(f"Season {season_number} poster.jpg 从 cover_url 下载")
                        except Exception as e:
                            logger.warning(f"Season {season_number} poster.jpg 从 cover_url 下载失败: {e}")

                # 最后回退：复制根目录的 poster.jpg（保证至少有海报）
                if not season_poster_path.exists():
                    root_poster = series_dir / POSTER_FILENAME
                    if root_poster.exists():
                        try:
                            shutil.copy2(root_poster, season_poster_path)
                            image_files.append(str(season_poster_path))
                            logger.warning(f"Season {season_number} poster.jpg 回退使用根目录 poster")
                        except Exception as e:
                            logger.warning(f"复制 poster.jpg 到 Season {season_number} 目录失败: {e}")

            # 生成 season{NN}-poster.jpg 到根目录（使用该季独立的 poster，对齐参考格式"未来日记"）
            season_numbered_poster_path = series_dir / SEASON_POSTER_FILENAME_PATTERN.format(season_number)
            if not season_numbered_poster_path.exists():
                if season_poster_path.exists():
                    try:
                        shutil.copy2(season_poster_path, season_numbered_poster_path)
                        image_files.append(str(season_numbered_poster_path))
                        logger.info(f"season{season_number:02d}-poster.jpg 已生成: {season_numbered_poster_path}")
                    except Exception as e:
                        logger.warning(f"生成 season{season_number:02d}-poster.jpg 失败: {e}")

            # 为 Season 目录生成独立的 thumb.jpg 和 landscape.jpg（横版预览图）
            # 对齐梅林传奇参考格式：每个 Season 目录都有独立的 thumb.jpg 和 landscape.jpg
            # 否则绿联NAS会回退到根目录的图片，导致所有季的预览图都一样
            season_cover_url = ""
            if season_metadata and hasattr(season_metadata[0], "cover_url") and season_metadata[0].cover_url:
                season_cover_url = season_metadata[0].cover_url

            # 生成 Season 目录的 landscape.jpg
            # 优先级：视频截帧 > thumbnail URL 下载 > 竖版海报裁剪
            season_landscape_path = season_dir / LANDSCAPE_FILENAME
            if not season_landscape_path.exists():
                # 1. 优先从该季视频文件截取真实画面（每集画面不同，预览图天然独立）
                season_video_file = None
                for f in sorted(season_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                        season_video_file = f
                        break
                if season_video_file:
                    try:
                        success = await self._extract_frame_from_video(
                            season_video_file, season_landscape_path, seek_pct=0.7
                        )
                        if success:
                            self._resize_to_standard(
                                season_landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT
                            )
                            image_files.append(str(season_landscape_path))
                            logger.info(f"Season {season_number} landscape.jpg 从视频截取")
                    except Exception as e:
                        logger.warning(f"Season {season_number} landscape.jpg 视频截取失败: {e}")

                # 2. 回退：从 thumbnail URL 下载
                if not season_landscape_path.exists() and season_cover_url:
                    thumbnail_url = self._get_horizontal_thumbnail_url(season_cover_url)
                    if thumbnail_url:
                        try:
                            success = await self._download_cover_as_jpg(thumbnail_url, season_landscape_path)
                            if success:
                                self._resize_to_standard(
                                    season_landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT
                                )
                                image_files.append(str(season_landscape_path))
                                logger.info(f"Season {season_number} landscape.jpg 从 thumbnail URL 下载")
                        except Exception as e:
                            logger.warning(f"Season {season_number} landscape.jpg 下载失败: {e}")

                # 3. 最后回退：从该季竖版海报裁剪（海报各季不同，裁剪后预览图也不同）
                if not season_landscape_path.exists() and season_poster_path.exists():
                    try:
                        success = self._crop_landscape_from_poster(
                            season_poster_path, season_landscape_path
                        )
                        if success:
                            self._resize_to_standard(
                                season_landscape_path, LANDSCAPE_STANDARD_WIDTH, LANDSCAPE_STANDARD_HEIGHT
                            )
                            image_files.append(str(season_landscape_path))
                            logger.info(f"Season {season_number} landscape.jpg 从 poster.jpg 裁剪生成")
                    except Exception as e:
                        logger.warning(f"Season {season_number} landscape.jpg 从海报裁剪失败: {e}")

            # 生成 Season 目录的 thumb.jpg（复制 landscape.jpg）
            season_thumb_path = season_dir / THUMB_FILENAME
            if not season_thumb_path.exists() and season_landscape_path.exists():
                try:
                    shutil.copy2(season_landscape_path, season_thumb_path)
                    image_files.append(str(season_thumb_path))
                    logger.info(f"Season {season_number} thumb.jpg 从 landscape.jpg 复制")
                except Exception as e:
                    logger.warning(f"Season {season_number} thumb.jpg 复制失败: {e}")

        # 10. 为每集生成 NFO 和缩略图
        for i, entry in enumerate(video_entries):
            video_id = entry["video_id"]
            mapping = episode_mapping.get(video_id)
            if not mapping:
                continue

            season_number = mapping["season"]
            episode_num = mapping["episode"]
            season_str = f"S{season_number:02d}"
            episode_str = f"E{episode_num:02d}"
            season_ep_pattern = f"{season_str}{episode_str}"

            meta = vid_to_meta.get(video_id)

            # 确定该集所在的 Season 目录
            season_dir = series_dir / f"{SEASON_DIR_PREFIX}{season_number}"
            season_dir.mkdir(parents=True, exist_ok=True)

            # 清理带年份后缀的旧文件（NFO、JPG 等）
            for old_file in season_dir.iterdir():
                if old_file.is_file() and season_ep_pattern in old_file.name:
                    if re.search(r'\(\d{4}\)', old_file.stem):
                        try:
                            old_file.unlink()
                            logger.info(f"清理带年份后缀的旧文件: {old_file.name}")
                        except Exception:
                            pass

            # 单集NFO（文件名：番剧名 - S01E01 - 第 1 集.nfo）
            episode_nfo_content = self.generate_episode_nfo(
                meta, season_number, episode_num, series_name=series_name_no_year
            )
            episode_filename = (
                f"{safe_series_name} - {season_str}{episode_str} - 第 {episode_num} 集"
            )

            episode_nfo_path = season_dir / f"{episode_filename}.nfo"
            await self._write_nfo_file(episode_nfo_path, episode_nfo_content)
            nfo_files.append(str(episode_nfo_path))

            # 单集封面图（v3.3.5：优先用每集自己的 cover_url 竖版海报）
            # 文件名：番剧名 - S01E01 - 第 1 集.jpg，与视频同名
            episode_cover_url = ""
            if meta and hasattr(meta, "cover_url") and meta.cover_url:
                episode_cover_url = meta.cover_url
            # v3.6.3: force_regenerate 由调用方控制（自动刮削复用已有封面，手动/批量刮削强制刷新）
            thumb_success = await self.generate_episode_thumb(
                season_dir, season_number, episode_num, episode_cover_url,
                series_name=series_name_no_year,
                force_regenerate=force_regenerate_covers
            )
            if thumb_success:
                image_files.append(str(season_dir / f"{episode_filename}.jpg"))

        return nfo_files, image_files

    async def _generate_movie_files(
        self,
        series_dir: Path,
        series_name: str,
        video_entries: List[Dict],
        metadata_list: List[Optional[Any]]
    ) -> tuple:
        """生成电影模式的NFO和图片文件"""
        nfo_files = []
        image_files = []

        # 对于电影模式，只为第一个视频生成NFO
        meta = metadata_list[0] if metadata_list else None
        video_id = video_entries[0]["video_id"] if video_entries else ""

        # 生成 movie.nfo
        movie_nfo_content = self.generate_movie_nfo(meta, video_id)
        movie_nfo_path = series_dir / MOVIE_NFO_FILENAME
        await self._write_nfo_file(movie_nfo_path, movie_nfo_content)
        nfo_files.append(str(movie_nfo_path))

        # 生成 poster.jpg
        cover_url = ""
        if meta and hasattr(meta, "cover_url") and meta.cover_url:
            cover_url = meta.cover_url
        poster_success = await self.generate_poster(series_dir, cover_url)
        if poster_success:
            image_files.append(str(series_dir / POSTER_FILENAME))

        # 生成 backdrop.jpg
        backdrop_success = await self.generate_backdrop(series_dir, cover_url)
        if backdrop_success:
            image_files.append(str(series_dir / BACKDROP_FILENAME))

        # 生成 fanart.jpg（复制 backdrop）
        fanart_success = await self.generate_fanart(series_dir, cover_url)
        if fanart_success:
            image_files.append(str(series_dir / FANART_FILENAME))

        # 生成 landscape.jpg
        landscape_success = await self.generate_landscape(series_dir, cover_url)
        if landscape_success:
            image_files.append(str(series_dir / LANDSCAPE_FILENAME))

        # 生成 thumb.jpg
        thumb_success = await self.generate_thumb(series_dir, cover_url)
        if thumb_success:
            image_files.append(str(series_dir / THUMB_FILENAME))

        # 生成 banner.jpg
        banner_success = await self.generate_banner(series_dir, cover_url)
        if banner_success:
            image_files.append(str(series_dir / BANNER_FILENAME))

        return nfo_files, image_files

    def _scan_series_directory(self, series_dir: Path) -> List[Dict]:
        """
        扫描番剧目录，返回视频文件列表及解析出的 video_id

        支持两种目录结构：
        1. 扁平结构: 番剧名/video_id_subtitle.mp4
        2. Season结构: 番剧名/Season 1/S01E01.mp4
           多季结构: 番剧名/Season 1/... + 番剧名/Season 2/...

        每个条目包含 season_number，从 Season 子目录名解析（如 "Season 2" → 2），
        扁平结构中的文件默认为第 1 季。
        """
        entries = []

        # 扫描根目录（非 Season 子目录的视频文件，默认为第 1 季）
        for f in series_dir.iterdir():
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                video_id = self._extract_video_id(f.stem)
                # 如果无法从文件名提取 video_id，尝试从 NFO 文件查找
                if not video_id or not video_id.isdigit():
                    nfo_video_id = self._lookup_video_id_from_nfo(f)
                    if nfo_video_id:
                        video_id = nfo_video_id
                entries.append({
                    "file_path": str(f),
                    "filename": f.name,
                    "video_id": video_id,
                    "is_season_subdir": False,
                    "season_number": 1
                })

        # 扫描 Season 子目录
        for sub in series_dir.iterdir():
            if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                # 从目录名解析季号（如 "Season 2" → 2）
                season_number = 1
                season_match = re.match(r'^Season\s+(\d+)$', sub.name, re.IGNORECASE)
                if season_match:
                    season_number = int(season_match.group(1))
                for f in sub.iterdir():
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                        video_id = self._extract_video_id(f.stem)
                        # 如果无法从文件名提取 video_id，尝试从 NFO 文件查找
                        if not video_id or not video_id.isdigit():
                            nfo_video_id = self._lookup_video_id_from_nfo(f)
                            if nfo_video_id:
                                video_id = nfo_video_id
                        entries.append({
                            "file_path": str(f),
                            "filename": f.name,
                            "video_id": video_id,
                            "is_season_subdir": True,
                            "season_number": season_number
                        })

        return entries

    def _extract_video_id(self, filename_stem: str) -> str:
        """
        从文件名中提取 video_id

        格式1: {video_id}_{subtitle}  → video_id
        格式2: S01E01                → 空字符串（需要通过NFO查找）
        格式3: 番剧名 - S01E01 - 第 1 集  → 空字符串（需要通过NFO查找）
        """
        # 尝试匹配 video_id_ 前缀
        match = re.match(r'^([a-zA-Z0-9]+?)_(.+)$', filename_stem)
        if match:
            candidate_id = match.group(1)
            if len(candidate_id) <= 20:
                return candidate_id

        # 尝试匹配纯 S01E01 格式
        if re.match(r'^S\d+E\d+$', filename_stem, re.IGNORECASE):
            return ""

        # 尝试匹配 "番剧名 - S01E01 - 第 N 集" 格式（刮削后的重命名格式）
        if re.search(r'S\d+E\d+', filename_stem, re.IGNORECASE):
            return ""

        # 如果都不匹配，使用整个文件名作为ID
        return filename_stem

    def _lookup_video_id_from_nfo(self, video_path: Path) -> str:
        """
        从同名 NFO 文件中查找 video_id

        NFO 文件中的 uniqueid 字段存储了 video_id，
        例如: <uniqueid type="hanime" default="true">13007</uniqueid>
        """
        nfo_path = video_path.with_suffix(".nfo")
        if not nfo_path.exists():
            return ""
        try:
            tree = ET.parse(str(nfo_path))
            root = tree.getroot()
            # 查找 uniqueid 标签
            uniqueid_elem = root.find("uniqueid")
            if uniqueid_elem is not None and uniqueid_elem.text:
                vid = uniqueid_elem.text.strip()
                # 确认是有效的 video_id（纯数字）
                if vid.isdigit():
                    return vid
        except Exception as e:
            logger.warning(f"从 NFO 查找 video_id 失败: {nfo_path} - {e}")
        return ""

    async def _lookup_video_id_from_db(self, file_path: Path) -> str:
        """
        从数据库下载记录中查找 video_id

        通过文件名匹配 downloads 表中的 filename 字段。
        """
        try:
            import aiosqlite
            db_path = settings.DB_PATH / "downloads.db"
            if not db_path.exists():
                return ""
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                # 尝试通过文件名匹配
                filename = file_path.name
                # 先尝试精确匹配 video_id (从文件名开头提取数字)
                async with conn.execute(
                    "SELECT video_id FROM downloads WHERE filename LIKE ? AND status = 'completed'",
                    (f"%{filename}%",)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and row['video_id'].isdigit():
                        return row['video_id']
                # 再尝试用文件名的 stem 匹配
                async with conn.execute(
                    "SELECT video_id FROM downloads WHERE filename LIKE ? AND status = 'completed'",
                    (f"%{file_path.stem}%",)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and row['video_id'].isdigit():
                        return row['video_id']
        except Exception as e:
            logger.warning(f"从数据库查找 video_id 失败: {file_path.name} - {e}")
        return ""

    def _determine_episode_number(
        self,
        video_entries: List[Dict],
        metadata_list: Optional[List[Optional[Any]]] = None
    ) -> Dict[str, Dict]:
        """
        确定每个视频的季号和集号

        返回映射: video_id -> {"season": N, "episode": M}

        一季多集策略（v3.3.3 回归标准电视剧结构）：
        - 所有同系列视频统一放入 Season 1
        - 所有的 season 固定为 1，对齐绿联NAS标准电视剧识别格式

        集号识别优先级（v3.3.4 修正）：
        1. 从视频元数据（title/subtitle）提取真实集号 ← 最高优先级
           - 支持"第十一話"→11、"第2話"→2、"Episode 5"→5
           - 支持中文数字（一/二/.../十一/.../九十九）
           - 支持罗马数字、文字标签（前編=1, 後編=2 等）
        2. 从文件名前缀 video_id_subtitle.mp4 中提取标题再识别
        3. 从文件名 S01Exx 格式提取（仅用于已刮削过的旧数据回退）
        4. 无法识别时按文件路径排序分配 E01, E02, E03...

        冲突解决：真实集号已被占用时递增到下一个可用位置。

        注意（v3.3.4 修正）：
        旧版本优先从文件名 S01Exx 提取集号，导致旧刮削数据中错误的
        S01E01（实际是第十一話）无法被修正为 S01E11。现在改为
        元数据真实集号优先，文件名集号仅作回退。
        """
        episode_mapping: Dict[str, Dict] = {}

        # 按文件路径排序，确保集号分配稳定
        sorted_entries = sorted(video_entries, key=lambda x: x["file_path"])

        # 构建 video_id -> metadata 的映射
        meta_map: Dict[str, Any] = {}
        if metadata_list:
            for i, entry in enumerate(video_entries):
                if i < len(metadata_list) and metadata_list[i]:
                    vid = entry.get("video_id", "")
                    if vid:
                        meta_map[vid] = metadata_list[i]

        # 收集已解析的集号
        used_episodes: Set[int] = set()
        regular_entries: List[Dict] = []

        for entry in sorted_entries:
            filename = entry["filename"]
            video_id = entry["video_id"]
            real_episode = 0
            file_episode = 0  # 文件名中的 S01Exx 集号（仅作回退）

            # 1. 优先从元数据（title/subtitle）提取真实集号
            meta = meta_map.get(video_id)
            if meta:
                title = getattr(meta, "title", "") or ""
                subtitle = getattr(meta, "subtitle", "") or ""
                real_episode = self._extract_episode_number_from_metadata(title, subtitle)
                logger.info(f"集号识别[{video_id}]: 从元数据提取, "
                          f"title='{title[:40]}', subtitle='{subtitle[:40]}', "
                          f"识别集号={real_episode}")

            # 2. 如果元数据没有，从文件名 video_id_subtitle.mp4 中提取标题再识别
            if real_episode == 0:
                fn_stem = Path(entry["file_path"]).stem
                if "_" in fn_stem:
                    title_from_filename = fn_stem.split("_", 1)[1]
                    real_episode = self._extract_episode_number_from_metadata(
                        title_from_filename, ""
                    )
                    if real_episode > 0:
                        logger.info(f"集号识别[{video_id}]: 从文件名标题提取, "
                                  f"title='{title_from_filename[:40]}', "
                                  f"识别集号={real_episode}")

            # 3. 如果真实集号识别失败，回退到文件名 S01Exx 格式
            if real_episode == 0:
                match = re.search(r'S\d+E(\d+)', filename, re.IGNORECASE)
                if match:
                    file_episode = int(match.group(1))
                    logger.info(f"集号识别[{video_id}]: 真实集号无法识别，"
                              f"回退到文件名 S01Exx={file_episode}")

            # 选择最终集号：真实集号优先，回退到文件名集号
            resolved_episode = real_episode if real_episode > 0 else file_episode

            if resolved_episode > 0:
                episode_num = resolved_episode
                # 冲突时递增
                while episode_num in used_episodes:
                    episode_num += 1
                used_episodes.add(episode_num)
                episode_mapping[video_id] = {"season": 1, "episode": episode_num}
            else:
                regular_entries.append(entry)

        # 为未解析的条目按上映时间排序后分配集号
        # v3.4.9: 按上传日期排序，越早发布的集号越小
        # 这样即使先下载第二集再下载第一集，刮削后第一集仍然分配 E01
        max_episode = max(used_episodes, default=0)
        if regular_entries:
            # 按 upload_date 排序（从 metadata 中获取）
            def _get_upload_date(entry: Dict) -> str:
                """获取视频上传日期，用于排序"""
                vid = entry.get("video_id", "")
                meta = meta_map.get(vid)
                if meta and hasattr(meta, "upload_date") and meta.upload_date:
                    ud = meta.upload_date
                    if isinstance(ud, (datetime, date)):
                        return ud.isoformat()
                    return str(ud)
                return ""

            # 按日期排序，无日期的排在最后（保持原始顺序）
            regular_entries.sort(key=lambda e: _get_upload_date(e) or "zzz")

        for entry in regular_entries:
            max_episode += 1
            episode_mapping[entry["video_id"]] = {
                "season": 1,
                "episode": max_episode
            }

        return episode_mapping

    def _extract_episode_number_from_metadata(self, title: str, subtitle: str) -> int:
        """
        从视频元数据 title/subtitle 中提取真实集号（阿拉伯数字），失败返回 0

        优先级（高→低）：
        1. "第N話/话/期/章/部/卷/篇/編" - 含中文数字 "第十一話"→11
        2. "Episode N"、"Ep. N"、"EP N"
        3. "＃N"、"#N"
        4. "Season N" - 仅作为集号参考
        5. 罗马数字 "第Ⅱ"、"Ⅱ"
        6. 文字标签（前編=1, 後編=2, 上巻=1, 下巻=2, OVA=99）
        7. 末尾阿拉伯数字 - 排除 1900-2099 的年份

        支持 1-99 的中文数字转换。
        """
        if not title and not subtitle:
            return 0

        # 中文数字到阿拉伯数字的转换表
        cn_digit_map = {
            '零': 0, '〇': 0,
            '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9,
        }

        def cn_to_arabic(cn: str) -> int:
            """中文数字转阿拉伯数字（1-99）"""
            if not cn:
                return 0
            if cn.isdigit():
                return int(cn)
            if len(cn) == 1:
                if cn == '十':
                    return 10
                return cn_digit_map.get(cn, 0)
            if cn.startswith('十'):
                return 10 + cn_digit_map.get(cn[1:], 0)
            if cn.endswith('十'):
                return cn_digit_map.get(cn[0], 0) * 10
            if '十' in cn:
                parts = cn.split('十')
                if len(parts) == 2:
                    return cn_digit_map.get(parts[0], 0) * 10 + cn_digit_map.get(parts[1], 0)
            return 0

        # subtitle 优先（中文副标题更规范）
        candidates = []
        if subtitle:
            candidates.append(subtitle)
        if title:
            candidates.append(title)

        # 文字标签到集号的映射
        # OVA/特典/番外：不再映射为99，返回0由系统按顺序分配
        label_to_episode = {
            '上卷': 1, '上巻': 1, '前篇': 1, '前編': 1, '上篇': 1,
            '中卷': 2, '中巻': 2, '中篇': 2, '中編': 2,
            '下卷': 3, '下巻': 3, '後篇': 3, '後編': 3, '下篇': 3,
            '后篇': 3, '后編': 3, '下编': 3,
        }

        for text in candidates:
            if not text:
                continue
            text = text.strip()

            # 1. "第N話/话/期/章/部/卷/篇/編" - 含中文数字和阿拉伯数字
            m = re.search(r'第\s*([零〇一二三四五六七八九十两\d]+)\s*[話话期章部卷篇編]', text)
            if m:
                num_str = m.group(1)
                if num_str.isdigit():
                    n = int(num_str)
                else:
                    n = cn_to_arabic(num_str)
                if n > 0:
                    return n

            # 2. "Episode N"、"Ep. N"、"EP N"
            m = re.search(r'(?:episode|ep\.?)\s*(\d+)', text, re.IGNORECASE)
            if m:
                return int(m.group(1))

            # 3. "＃N" 或 "#N"
            m = re.search(r'[＃#]\s*(\d+)', text)
            if m:
                return int(m.group(1))

            # 4. "Season N"
            m = re.search(r'[Ss]eason\s*(\d+)', text)
            if m:
                return int(m.group(1))

            # 5. 罗马数字
            roman_map = {'Ⅰ': 1, 'Ⅱ': 2, 'Ⅲ': 3, 'Ⅳ': 4, 'Ⅴ': 5,
                         'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
            m = re.search(r'第\s*([ⅠⅡⅢⅣⅤ]+)\s*[話话期章部]?', text)
            if m and m.group(1) in roman_map:
                return roman_map[m.group(1)]
            m = re.search(r'\s([ⅠⅡⅢⅣⅤ])\s*$', text)
            if m and m.group(1) in roman_map:
                return roman_map[m.group(1)]

            # 6. 文字标签
            for label in sorted(label_to_episode.keys(), key=len, reverse=True):
                if label in text:
                    return label_to_episode[label]

            # 7. 末尾阿拉伯数字（排除年份）
            text_no_bracket = re.sub(r'\s*\[[^\]]*\]\s*$', '', text).strip()
            m = re.search(r'(\d+)\s*$', text_no_bracket)
            if m:
                n = int(m.group(1))
                if not (1900 <= n <= 2099):
                    return n

        return 0

    def _cleanup_empty_series_directories(self, current_series_dir: Path) -> List[str]:
        """
        清理 DOWNLOAD_PATH 下的空残留目录（v3.3.4 新增）

        旧版本系列识别错误时，可能为同一系列创建多个目录，例如：
          ○○交配 第一話 毎日お世話してくれる彼女はエルフのお姫様
          ○○交配 第十一話 毎日お世話してくれる彼女はエルフのお姫様 前編 [中文字幕]
        系列识别修复后，这些目录的视频会被移到正确的目录，但空目录会残留。

        清理策略：
        1. 扫描 DOWNLOAD_PATH 下所有目录
        2. 跳过当前正在刮削的 series_dir（避免影响正在进行的流程）
        3. 跳过 Season 子目录（不属于独立系列）
        4. 跳过 COVER_PATH 等特殊目录
        5. 对每个其他目录，统计视频文件数量（包括 Season 子目录中的视频）
        6. 如果目录中没有视频文件，但包含 NFO/.jpg/.png 等附属文件（视频已被移走），
           则删除这些孤立附属文件和目录
        7. 完全空的目录也一并删除

        :param current_series_dir: 当前正在刮削的系列目录
        :return: 已清理的目录名列表（用于日志记录）
        """
        cleaned: List[str] = []

        try:
            download_path = settings.DOWNLOAD_PATH
            if not download_path.exists():
                return cleaned

            # 不需要清理的特殊目录
            special_dirs = {settings.COVER_PATH.name, "covers", ".covers"}
            current_dir_name = current_series_dir.name

            for series_dir in download_path.iterdir():
                if not series_dir.is_dir():
                    continue
                # 跳过当前正在刮削的目录
                if series_dir.name == current_dir_name:
                    continue
                # 跳过 Season 子目录（虽然这里不应该出现，但保险起见）
                if series_dir.name.startswith("Season "):
                    continue
                # 跳过特殊目录
                if series_dir.name in special_dirs:
                    continue
                # 跳过中央封面目录
                if series_dir == settings.COVER_PATH:
                    continue

                # 统计该目录下的视频文件（包括 Season 子目录）
                video_count = 0
                for f in series_dir.rglob("*"):
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                        video_count += 1
                        break  # 只要有视频就跳出

                if video_count > 0:
                    # 有视频，不能删除
                    continue

                # 该目录没有视频文件，但可能有孤立的附属文件
                # 检查是否真的需要清理：是否有 NFO/.jpg/.png 等附属文件
                has_attachments = False
                for f in series_dir.rglob("*"):
                    if f.is_file() and f.suffix.lower() in (
                        ".nfo", ".jpg", ".jpeg", ".png", ".webp"
                    ):
                        has_attachments = True
                        break

                # 如果目录完全空（没有任何文件），直接删除
                # 如果有孤立附属文件（视频已被移走），也清理
                try:
                    # 先尝试 rmdir（只对完全空的目录生效）
                    # 如果有内容，使用 shutil.rmtree
                    is_empty = True
                    for _ in series_dir.rglob("*"):
                        is_empty = False
                        break

                    if is_empty:
                        series_dir.rmdir()
                        logger.info(f"清理空目录: {series_dir.name}")
                        cleaned.append(series_dir.name)
                    elif has_attachments:
                        # 目录只有孤立附属文件（视频已被移走），删除整个目录
                        # 安全检查：再次确认没有视频文件
                        import shutil as _shutil
                        _shutil.rmtree(series_dir)
                        logger.info(f"清理残留附属文件目录: {series_dir.name}")
                        cleaned.append(series_dir.name)
                except Exception as e:
                    logger.warning(f"清理目录失败: {series_dir.name} - {e}")

        except Exception as e:
            logger.warning(f"扫描空残留目录失败: {e}")

        return cleaned

    async def _fetch_metadata(self, video_entries: List[Dict]) -> List[Optional[Any]]:
        """
        从VideoService获取每个视频的元数据

        v3.3.9: 如果启用翻译，会就地翻译元数据中的 description（简介）
        """
        from app.services.translation_service import translation_service

        metadata_list = []
        for entry in video_entries:
            video_id = entry["video_id"]
            if not video_id:
                metadata_list.append(None)
                continue
            try:
                detail = await self.video_service.get_video_detail(video_id)
                # v3.3.9: 启用翻译时，翻译简介
                if detail and settings.TRANSLATE_PLOT_ENABLED:
                    target_lang = settings.TRANSLATE_TARGET_LANG
                    if target_lang and target_lang != "off":
                        original_desc = getattr(detail, "description", "") or ""
                        if original_desc:
                            translated = await translation_service.translate(
                                original_desc, target_lang
                            )
                            if translated and translated != original_desc:
                                try:
                                    detail.description = translated
                                    logger.info(
                                        f"翻译简介 video_id={video_id}: "
                                        f"{len(original_desc)} -> {len(translated)} 字符 "
                                        f"(目标语言: {target_lang})"
                                    )
                                except Exception:
                                    # description 可能是 frozen，跳过
                                    pass
                metadata_list.append(detail)
            except Exception as e:
                logger.warning(f"获取视频元数据失败 video_id={video_id}: {e}")
                metadata_list.append(None)
        return metadata_list

    async def set_collection_poster(self, series_name: str, video_id: str) -> dict:
        """
        将指定剧集的封面设为合集海报

        查找该 video_id 对应的封面图片，将其复制/转换为合集目录的 poster.jpg，
        并同步更新 season01-poster.jpg（如存在）。

        v3.5.2 新增
        """
        series_dir = settings.DOWNLOAD_PATH / series_name
        if not series_dir.exists() or not series_dir.is_dir():
            return {"status": "error", "message": f"番剧目录不存在: {series_name}"}

        # 查找封面来源：优先从 COVER_PATH 查找，再从番剧目录中查找
        source_cover = None

        # 1. COVER_PATH 中查找 {video_id}.jpg
        central_cover = settings.COVER_PATH / f"{video_id}.jpg"
        if central_cover.exists():
            source_cover = central_cover
            logger.info(f"从 COVER_PATH 找到封面: {central_cover}")

        # 2. 番剧根目录中查找 {video_id}.jpg（刮削前可能在根目录）
        if not source_cover:
            root_cover = series_dir / f"{video_id}.jpg"
            if root_cover.exists():
                source_cover = root_cover
                logger.info(f"从番剧根目录找到封面: {root_cover}")

        # 3. Season 子目录中查找与该 video_id 相关的 .jpg 缩略图
        if not source_cover:
            for sub in series_dir.iterdir():
                if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                    # 查找刮削后的缩略图（与视频同名 .jpg）
                    for f in sub.iterdir():
                        if f.is_file() and f.suffix.lower() == ".jpg":
                            # 检查 NFO 中的 uniqueid 是否匹配 video_id
                            nfo_file = f.with_suffix(".nfo")
                            if nfo_file.exists():
                                try:
                                    nfo_content = nfo_file.read_text(encoding="utf-8")
                                    if f'<uniqueid type="hanime">{video_id}</uniqueid>' in nfo_content or \
                                       f'default="true">{video_id}</uniqueid>' in nfo_content:
                                        source_cover = f
                                        logger.info(f"从 Season 子目录找到封面: {f}")
                                        break
                                except Exception:
                                    pass
                    if source_cover:
                        break

        # 4. Season 子目录中查找 {video_id}.jpg
        if not source_cover:
            for sub in series_dir.iterdir():
                if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                    vid_cover = sub / f"{video_id}.jpg"
                    if vid_cover.exists():
                        source_cover = vid_cover
                        logger.info(f"从 Season 子目录找到 video_id 封面: {vid_cover}")
                        break

        if not source_cover:
            return {"status": "error", "message": f"未找到 video_id={video_id} 的封面文件"}

        # 复制/转换为 poster.jpg
        poster_path = series_dir / POSTER_FILENAME
        try:
            if source_cover.suffix.lower() != ".jpg" and settings.SCRAPE_CONVERT_COVER_JPG:
                success = self._convert_image_to_jpg(source_cover, poster_path)
                if not success:
                    return {"status": "error", "message": "封面转换 JPG 失败"}
            else:
                shutil.copy2(source_cover, poster_path)

            # 放大到标准尺寸
            self._upscale_to_standard(poster_path, POSTER_STANDARD_WIDTH, POSTER_STANDARD_HEIGHT)

            # 同步更新 season01-poster.jpg（如存在）
            season_poster_path = series_dir / SEASON_POSTER_FILENAME_PATTERN.format(1)
            if season_poster_path.exists():
                shutil.copy2(poster_path, season_poster_path)
                logger.info(f"已同步更新 season01-poster.jpg")

            # 同步更新所有 Season 目录里的 poster.jpg
            # 绿联 NAS 实际显示的是 Season 目录内的 poster.jpg
            for sub in series_dir.iterdir():
                if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                    season_poster = sub / POSTER_FILENAME
                    if season_poster.exists():
                        shutil.copy2(poster_path, season_poster)
                        logger.info(f"已同步更新 {sub.name}/poster.jpg")

            logger.info(f"合集海报已更新: {poster_path} (来源: {source_cover})")
            return {"status": "success", "message": f"合集海报已更新为 video_id={video_id} 的封面"}

        except Exception as e:
            logger.error(f"更新合集海报失败: {e}")
            return {"status": "error", "message": f"更新合集海报失败: {str(e)}"}

    def _find_existing_cover(self, series_dir: Path) -> Optional[Path]:
        """在番剧目录中查找已有的封面文件"""
        # 按优先级查找
        cover_candidates = [
            "poster.jpg", "poster.png", "poster.webp",
            "folder.jpg", "folder.png",
        ]
        for name in cover_candidates:
            path = series_dir / name
            if path.exists():
                return path

        # 排除所有刮削生成的图片文件名（包括 season01-poster.jpg 这类季海报）
        excluded_names = {
            POSTER_FILENAME, BACKDROP_FILENAME, FANART_FILENAME,
            LANDSCAPE_FILENAME, THUMB_FILENAME, BANNER_FILENAME,
            TVSHOW_NFO_FILENAME, MOVIE_NFO_FILENAME,
        }
        # season{NN}-poster.jpg 模式（季海报，刮削生成）
        excluded_patterns = [
            re.compile(r'^season\d+-poster\.(jpg|png|webp)$', re.IGNORECASE),
        ]

        # 查找 video_id.jpg 格式的封面
        for f in series_dir.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpg", ".png", ".webp"):
                if f.stem and not f.name.startswith("S") and f.name not in excluded_names:
                    # 排除 season{NN}-poster.jpg 这类文件
                    if any(p.match(f.name) for p in excluded_patterns):
                        continue
                    return f

        # 查找Season子目录中的封面
        for sub in series_dir.iterdir():
            if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                for f in sub.iterdir():
                    if f.is_file() and f.suffix.lower() in (".jpg", ".png", ".webp"):
                        return f

        return None

    async def _download_cover_as_jpg(self, cover_url: str, save_path: Path) -> bool:
        """
        下载封面并保存为JPG格式
        绿联影视中心仅识别JPG格式。

        使用 cf_bypasser 的 direct_client 下载（带正确的 headers 和代理配置），
        避免裸 httpx 无法绕过 Cloudflare 防护导致 403 错误。
        """
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 通过 cf_bypasser 的 direct_client 下载（带正确 headers 和代理）
            client = await cf_bypasser.direct_client
            response = await client.get(cover_url)
            if response.status_code != 200:
                logger.warning(f"下载封面失败: HTTP {response.status_code}, URL: {cover_url}")
                return False

            if settings.SCRAPE_CONVERT_COVER_JPG:
                # 转换为JPG
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
                    tmp.write(response.content)
                    tmp_path = Path(tmp.name)

                success = self._convert_to_jpg(tmp_path, save_path)
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return success
            else:
                save_path.write_bytes(response.content)
                return True

        except Exception as e:
            logger.error(f"下载封面异常: {e}")
            return False

    @staticmethod
    def _get_image_resolution(image_path: Path) -> int:
        """获取图片的分辨率（较长边像素数），失败返回0"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                return max(width, height)
        except Exception:
            return 0

    def _convert_to_jpg(self, source_path: Path, target_path: Path) -> bool:
        """使用Pillow将图片转换为JPG格式"""
        try:
            from PIL import Image

            with Image.open(source_path) as img:
                # 如果是RGBA模式，转换为RGB（JPG不支持透明通道）
                if img.mode in ("RGBA", "LA", "P"):
                    # 创建白色背景
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(target_path, "JPEG", quality=100, subsampling=0)
                return True

        except ImportError:
            logger.warning("Pillow未安装，无法转换图片格式，直接复制")
            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            logger.error(f"图片转换失败: {e}")
            return False

    def _convert_image_to_jpg(self, source_path: Path, target_path: Path) -> bool:
        """将已有图片文件转换为JPG格式"""
        return self._convert_to_jpg(source_path, target_path)

    # 需要清理空标签的日期字段（空标签会导致绿联显示 1970-01-01）
    # v3.3.9 修复：同时匹配两种空标签形式：
    #   1. 自闭合：<year/>、<premiered />
    #   2. 开闭合空内容：<year></year>、<premiered>   </premiered>
    _EMPTY_DATE_TAG_RE = re.compile(
        r'^\s*<(year|premiered|releasedate|aired|enddate)(\s[^>]*)?\s*/>\s*$'
        r'|^\s*<(year|premiered|releasedate|aired|enddate)(\s[^>]*)?\s*>\s*</\3\s*>\s*$',
        re.MULTILINE
    )

    async def _write_nfo_file(self, nfo_path: Path, content: str):
        """写入NFO文件（自动移除日期相关的空标签）"""
        try:
            nfo_path.parent.mkdir(parents=True, exist_ok=True)
            # 移除空日期标签，避免绿联影视中心将空值解析为 1970-01-01
            cleaned = self._EMPTY_DATE_TAG_RE.sub('', content)
            import aiofiles
            async with aiofiles.open(nfo_path, "w", encoding="utf-8") as f:
                await f.write(cleaned)
            logger.info(f"NFO文件已生成: {nfo_path}")
        except Exception as e:
            logger.error(f"写入NFO文件失败: {nfo_path} - {e}")

    @staticmethod
    def _sanitize_nfo_text(text: str) -> str:
        """清理NFO文本中的非法XML字符"""
        if not text:
            return ""
        # 移除XML 1.0不允许的控制字符（保留换行、制表符、回车）
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # 转义XML特殊字符（如果不在CDATA中）
        # 注意：ET会自动处理转义，这里只清理控制字符
        return text.strip()

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """处理文件名，移除非法字符"""
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
        return filename

    @staticmethod
    def _pretty_xml(root: ET.Element) -> str:
        """生成格式化的XML字符串，并对 plot/outline 标签内容包裹 CDATA"""
        rough_string = ET.tostring(root, encoding="unicode", xml_declaration=False)
        try:
            parsed = minidom.parseString(rough_string)
            pretty = parsed.toprettyxml(indent="  ")
            # 移除minidom添加的额外XML声明
            lines = pretty.split("\n")
            if lines and lines[0].startswith("<?xml"):
                lines = lines[1:]
            content = NFO_XML_DECLARATION + "\n".join(lines)
            # 对需要 CDATA 包裹的标签进行处理
            content = ScrapeService._wrap_cdata(content, CDATA_TAGS)
            # episodeguide 标签中的引号不应被 XML 转义
            # 参考目录（国色芳华、未来日记等）的 episodeguide 都是原始 JSON 格式
            # minidom 会自动转义引号为 &quot;，需要恢复
            content = re.sub(
                r'(<episodeguide>)(.*?)(</episodeguide>)',
                lambda m: m.group(1) + m.group(2).replace('&quot;', '"') + m.group(3),
                content,
                flags=re.DOTALL
            )
            return content
        except Exception:
            content = NFO_XML_DECLARATION + rough_string
            content = ScrapeService._wrap_cdata(content, CDATA_TAGS)
            # episodeguide 反转义（异常分支也需要）
            content = re.sub(
                r'(<episodeguide>)(.*?)(</episodeguide>)',
                lambda m: m.group(1) + m.group(2).replace('&quot;', '"') + m.group(3),
                content,
                flags=re.DOTALL
            )
            return content

    @staticmethod
    def _wrap_cdata(xml_string: str, tags: List[str]) -> str:
        """
        将指定标签的内容用 CDATA 包裹

        Python 标准库 xml.etree.ElementTree 不直接支持 CDATA，
        通过后处理将 <tag>内容</tag> 转为 <tag><![CDATA[内容]]></tag>。
        空标签（<tag></tag> 或 <tag />）保持不变。
        """
        for tag in tags:
            # 匹配 <tag>非空内容</tag>（不匹配空标签和自闭合标签）
            pattern = rf'<{tag}>(.+?)</{tag}>'

            def replace(match):
                content = match.group(1)
                # 如果已经是 CDATA，不重复包裹
                if content.strip().startswith('<![CDATA['):
                    return match.group(0)
                # 反转义 XML 实体（ET 会自动转义特殊字符）
                content = (content
                           .replace('&lt;', '<')
                           .replace('&gt;', '>')
                           .replace('&quot;', '"')
                           .replace('&apos;', "'")
                           .replace('&amp;', '&'))
                # 处理 CDATA 结束序列（极少见，但需正确转义）
                content = content.replace(']]>', ']]]]><![CDATA[>')
                return f'<{tag}><![CDATA[{content}]]></{tag}>'

            xml_string = re.sub(pattern, replace, xml_string, flags=re.DOTALL)
        return xml_string

    @staticmethod
    def _is_landscape_image(image_path: Path) -> bool:
        """判断图片是否为横版（宽 >= 高）"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                return width >= height
        except Exception:
            return False


# 创建刮削服务实例
scrape_service = ScrapeService()
