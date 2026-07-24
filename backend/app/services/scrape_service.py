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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from xml.dom import minidom

from app.config import settings, logger
from app.models.scrape import (
    ScrapeMode, ScrapeResult, ScrapableSeries, NfoPreview
)
from app.services.video_service import VideoService
from app.services.download_service import download_manager

# NFO XML 声明
NFO_XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

# 成人内容分级
MPAA_ADULT_RATING = "NC-17"

# 绿联NAS影视中心支持的图片格式（仅JPG！PNG不被识别）
SUPPORTED_IMAGE_FORMAT = "jpg"

# 视频文件扩展名
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".wmv", ".flv", ".ts"}

# NFO文件名常量
TVSHOW_NFO_FILENAME = "tvshow.nfo"
MOVIE_NFO_FILENAME = "movie.nfo"
SEASON_DIR_PREFIX = "Season "


class ScrapeService:
    """NFO刮削服务"""

    def __init__(self):
        self.video_service = VideoService()

    # ==================== 主流程 ====================

    async def scrape_series(
        self,
        series_name: str,
        scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW,
        is_rename_file: bool = True,
        is_reorganize_directory: bool = True
    ) -> ScrapeResult:
        """
        对一个番剧系列执行刮削

        流程：
        1. 扫描番剧目录获取所有视频文件
        2. 从文件名解析 video_id
        3. 从 VideoService 获取元数据
        4. 生成 NFO 文件和图片
        5. 可选：重命名文件和重组目录
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

            # 2. 获取元数据
            metadata_list = await self._fetch_metadata(video_entries)

            # 3. 确定集号
            episode_mapping = self._determine_episode_number(video_entries)

            # 4. 生成 NFO 和图片
            if scrape_mode == ScrapeMode.TV_SHOW:
                nfo_files, image_files = await self._generate_tv_show_files(
                    series_dir, series_name, video_entries,
                    metadata_list, episode_mapping
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
                renamed = await self._reorganize_files(
                    series_dir, series_name, video_entries,
                    episode_mapping, scrape_mode,
                    is_rename_file, is_reorganize_directory
                )
                result.renamed_files = renamed

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

        只生成当前视频的单集NFO，
        如果番剧目录还没有tvshow.nfo则一并生成。
        """
        try:
            # 查找该 video_id 对应的下载记录
            download_info = None
            for series_dir in settings.DOWNLOAD_PATH.iterdir():
                if not series_dir.is_dir():
                    continue
                for video_file in series_dir.iterdir():
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
            result = await self.scrape_series(
                series_name=series_name,
                scrape_mode=scrape_mode,
                is_rename_file=settings.SCRAPE_RENAME_FILE,
                is_reorganize_directory=settings.SCRAPE_REORGANIZE_DIRECTORY
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
        """批量刮削所有番剧目录"""
        if series_names is None or len(series_names) == 0:
            # 扫描所有番剧目录
            series_names = []
            for item in settings.DOWNLOAD_PATH.iterdir():
                if item.is_dir():
                    # 检查目录中是否有视频文件
                    has_video = any(
                        f.suffix.lower() in VIDEO_EXTENSIONS
                        for f in item.iterdir() if f.is_file()
                    ) or any(
                        f.suffix.lower() in VIDEO_EXTENSIONS
                        for sub in item.iterdir() if sub.is_dir()
                        for f in sub.iterdir() if f.is_file()
                    )
                    if has_video:
                        series_names.append(item.name)

        results = []
        for name in series_names:
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

        从同一系列的所有视频元数据中聚合信息
        """
        root = ET.Element("tvshow")

        # 标题
        title_elem = ET.SubElement(root, "title")
        title_elem.text = self._sanitize_nfo_text(series_title)

        originaltitle_elem = ET.SubElement(root, "originaltitle")
        originaltitle_elem.text = self._sanitize_nfo_text(series_title)

        sorttitle_elem = ET.SubElement(root, "sorttitle")
        sorttitle_elem.text = self._sanitize_nfo_text(series_title)

        # 描述（使用第一个有描述的视频）
        plot_text = ""
        for meta in metadata_list:
            if meta and hasattr(meta, "description") and meta.description:
                plot_text = meta.description
                break
        if plot_text:
            plot_elem = ET.SubElement(root, "plot")
            plot_elem.text = self._sanitize_nfo_text(plot_text)

        # 分级（成人内容固定为 NC-17）
        mpaa_elem = ET.SubElement(root, "mpaa")
        mpaa_elem.text = MPAA_ADULT_RATING

        # 日期和年份
        earliest_date = None
        for meta in metadata_list:
            if meta and hasattr(meta, "upload_date") and meta.upload_date:
                try:
                    if isinstance(meta.upload_date, datetime):
                        date_val = meta.upload_date
                    else:
                        date_val = datetime.fromisoformat(str(meta.upload_date))
                    if earliest_date is None or date_val < earliest_date:
                        earliest_date = date_val
                except (ValueError, TypeError):
                    pass

        if earliest_date:
            premiered_elem = ET.SubElement(root, "premiered")
            premiered_elem.text = earliest_date.strftime("%Y-%m-%d")
            year_elem = ET.SubElement(root, "year")
            year_elem.text = str(earliest_date.year)

        # 制作公司（去重合并）
        studios_added: Set[str] = set()
        for meta in metadata_list:
            if meta and hasattr(meta, "studio") and meta.studio:
                studio_name = meta.studio.name if hasattr(meta.studio, "name") else str(meta.studio)
                if studio_name and studio_name not in studios_added:
                    studio_elem = ET.SubElement(root, "studio")
                    studio_elem.text = self._sanitize_nfo_text(studio_name)
                    studios_added.add(studio_name)

        # 类型标签（固定添加"动画"和"成人"，再加实际标签）
        genres_added: Set[str] = {"动画", "成人", "Animation", "Adult"}
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

        # 标签
        tags_added: Set[str] = set()
        for meta in metadata_list:
            if meta and hasattr(meta, "tags") and meta.tags:
                for tag in meta.tags:
                    tag_name = tag.name if hasattr(tag, "name") else str(tag)
                    if tag_name and tag_name not in tags_added:
                        tag_elem = ET.SubElement(root, "tag")
                        tag_elem.text = self._sanitize_nfo_text(tag_name)
                        tags_added.add(tag_name)

        # 唯一标识符
        if video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.set("default", "true")
            uniqueid_elem.text = video_id

        # 海报图
        thumb_elem = ET.SubElement(root, "thumb")
        thumb_elem.set("aspect", "poster")
        thumb_elem.set("preview", "poster.jpg")
        thumb_elem.text = "poster.jpg"

        # 背景图
        fanart_elem = ET.SubElement(root, "fanart")
        fanart_thumb = ET.SubElement(fanart_elem, "thumb")
        fanart_thumb.set("preview", "fanart.jpg")
        fanart_thumb.text = "fanart.jpg"

        return self._pretty_xml(root)

    def generate_episode_nfo(
        self,
        video_detail: Optional[Any],
        season_number: int,
        episode_number: int,
        episode_title: Optional[str] = None
    ) -> str:
        """生成单集 .nfo 文件"""
        root = ET.Element("episodedetails")

        # 标题
        title_text = episode_title or f"第{episode_number}集"
        if video_detail and hasattr(video_detail, "subtitle") and video_detail.subtitle:
            title_text = video_detail.subtitle
        title_elem = ET.SubElement(root, "title")
        title_elem.text = self._sanitize_nfo_text(title_text)

        # 季号和集号
        season_elem = ET.SubElement(root, "season")
        season_elem.text = str(season_number)
        episode_elem = ET.SubElement(root, "episode")
        episode_elem.text = str(episode_number)

        # 描述
        if video_detail and hasattr(video_detail, "description") and video_detail.description:
            plot_elem = ET.SubElement(root, "plot")
            plot_elem.text = self._sanitize_nfo_text(video_detail.description)

        # 播出日期
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, datetime):
                    date_str = video_detail.upload_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(video_detail.upload_date)[:10]
                aired_elem = ET.SubElement(root, "aired")
                aired_elem.text = date_str
            except (ValueError, TypeError):
                pass

        # 单集缩略图
        season_str = f"S{season_number:02d}"
        episode_str = f"E{episode_number:02d}"
        thumb_filename = f"{season_str}{episode_str}-thumb.jpg"
        thumb_elem = ET.SubElement(root, "thumb")
        thumb_elem.set("aspect", "thumb")
        thumb_elem.set("preview", thumb_filename)
        thumb_elem.text = thumb_filename

        return self._pretty_xml(root)

    def generate_movie_nfo(
        self,
        video_detail: Optional[Any],
        video_id: str = ""
    ) -> str:
        """生成 movie.nfo（电影模式）"""
        root = ET.Element("movie")

        # 标题
        title_text = ""
        if video_detail:
            if hasattr(video_detail, "title") and video_detail.title:
                title_text = video_detail.title
            if hasattr(video_detail, "subtitle") and video_detail.subtitle:
                title_text = f"{title_text} {video_detail.subtitle}" if title_text else video_detail.subtitle

        if not title_text:
            title_text = "Unknown"

        title_elem = ET.SubElement(root, "title")
        title_elem.text = self._sanitize_nfo_text(title_text)

        originaltitle_elem = ET.SubElement(root, "originaltitle")
        originaltitle_elem.text = self._sanitize_nfo_text(title_text)

        # 描述
        if video_detail and hasattr(video_detail, "description") and video_detail.description:
            plot_elem = ET.SubElement(root, "plot")
            plot_elem.text = self._sanitize_nfo_text(video_detail.description)

        # 分级
        mpaa_elem = ET.SubElement(root, "mpaa")
        mpaa_elem.text = MPAA_ADULT_RATING

        # 日期和年份
        if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
            try:
                if isinstance(video_detail.upload_date, datetime):
                    date_val = video_detail.upload_date
                else:
                    date_val = datetime.fromisoformat(str(video_detail.upload_date))
                premiered_elem = ET.SubElement(root, "premiered")
                premiered_elem.text = date_val.strftime("%Y-%m-%d")
                year_elem = ET.SubElement(root, "year")
                year_elem.text = str(date_val.year)
            except (ValueError, TypeError):
                pass

        # 制作公司
        if video_detail and hasattr(video_detail, "studio") and video_detail.studio:
            studio_name = video_detail.studio.name if hasattr(video_detail.studio, "name") else str(video_detail.studio)
            if studio_name:
                studio_elem = ET.SubElement(root, "studio")
                studio_elem.text = self._sanitize_nfo_text(studio_name)

        # 类型
        for fixed_genre in ["动画", "成人"]:
            genre_elem = ET.SubElement(root, "genre")
            genre_elem.text = fixed_genre

        # 标签
        if video_detail and hasattr(video_detail, "tags") and video_detail.tags:
            for tag in video_detail.tags:
                tag_name = tag.name if hasattr(tag, "name") else str(tag)
                if tag_name:
                    tag_elem = ET.SubElement(root, "tag")
                    tag_elem.text = self._sanitize_nfo_text(tag_name)

        # 唯一标识符
        if video_id:
            uniqueid_elem = ET.SubElement(root, "uniqueid")
            uniqueid_elem.set("type", "hanime")
            uniqueid_elem.set("default", "true")
            uniqueid_elem.text = video_id

        # 海报图
        thumb_elem = ET.SubElement(root, "thumb")
        thumb_elem.set("aspect", "poster")
        thumb_elem.set("preview", "poster.jpg")
        thumb_elem.text = "poster.jpg"

        # 背景图
        fanart_elem = ET.SubElement(root, "fanart")
        fanart_thumb = ET.SubElement(fanart_elem, "thumb")
        fanart_thumb.set("preview", "fanart.jpg")
        fanart_thumb.text = "fanart.jpg"

        return self._pretty_xml(root)

    # ==================== 图片处理 ====================

    async def generate_poster(
        self,
        series_dir: Path,
        cover_url: str
    ) -> bool:
        """
        生成 poster.jpg（封面海报）

        绿联影视中心仅识别JPG格式封面！
        1. 优先使用已有封面文件
        2. 否则下载并转换为JPG
        """
        poster_path = series_dir / "poster.jpg"

        # 如果已有 poster.jpg，跳过
        if poster_path.exists():
            logger.info(f"poster.jpg 已存在: {poster_path}")
            return True

        # 尝试从已有封面文件复制/转换
        existing_cover = self._find_existing_cover(series_dir)
        if existing_cover:
            try:
                if settings.SCRAPE_CONVERT_COVER_JPG and existing_cover.suffix.lower() != ".jpg":
                    # 需要转换为JPG
                    success = self._convert_image_to_jpg(existing_cover, poster_path)
                    if success:
                        logger.info(f"封面转换成功: {existing_cover} -> {poster_path}")
                        return True
                else:
                    # 直接复制
                    shutil.copy2(existing_cover, poster_path)
                    logger.info(f"封面复制成功: {existing_cover} -> {poster_path}")
                    return True
            except Exception as e:
                logger.warning(f"封面处理失败: {e}")

        # 从URL下载
        if cover_url:
            try:
                success = await self._download_cover_as_jpg(cover_url, poster_path)
                if success:
                    logger.success(f"封面下载成功: {poster_path}")
                    return True
            except Exception as e:
                logger.warning(f"封面下载失败: {e}")

        return False

    async def generate_episode_thumb(
        self,
        season_dir: Path,
        season_number: int,
        episode_number: int,
        cover_url: str = ""
    ) -> bool:
        """生成单集缩略图 S01E01-thumb.jpg"""
        season_str = f"S{season_number:02d}"
        episode_str = f"E{episode_number:02d}"
        thumb_filename = f"{season_str}{episode_str}-thumb.jpg"
        thumb_path = season_dir / thumb_filename

        if thumb_path.exists():
            return True

        if cover_url:
            try:
                success = await self._download_cover_as_jpg(cover_url, thumb_path)
                if success:
                    logger.info(f"单集缩略图下载成功: {thumb_path}")
                    return True
            except Exception as e:
                logger.warning(f"单集缩略图下载失败: {e}")

        return False

    async def generate_fanart(
        self,
        series_dir: Path,
        cover_url: str = ""
    ) -> bool:
        """
        生成 fanart.jpg（背景图）

        如果没有专门的背景图，使用封面作为替代
        """
        fanart_path = series_dir / "fanart.jpg"

        if fanart_path.exists():
            return True

        # 尝试使用 poster.jpg 作为 fanart
        poster_path = series_dir / "poster.jpg"
        if poster_path.exists():
            try:
                shutil.copy2(poster_path, fanart_path)
                logger.info(f"fanart.jpg 从 poster.jpg 生成: {fanart_path}")
                return True
            except Exception as e:
                logger.warning(f"生成fanart失败: {e}")

        # 从URL下载
        if cover_url:
            try:
                success = await self._download_cover_as_jpg(cover_url, fanart_path)
                return success
            except Exception as e:
                logger.warning(f"fanart下载失败: {e}")

        return False

    # ==================== 文件重命名和目录重组 ====================

    async def _reorganize_files(
        self,
        series_dir: Path,
        series_name: str,
        video_entries: List[Dict],
        episode_mapping: Dict[str, int],
        scrape_mode: ScrapeMode,
        is_rename_file: bool,
        is_reorganize_directory: bool
    ) -> List[str]:
        """
        重命名视频文件并重组目录结构

        电视剧模式：
          原始: 番剧名/video_id_subtitle.mp4
          目标: 番剧名/Season 01/S01E01.mp4

        电影模式：
          原始: 番剧名/video_id_subtitle.mp4
          目标: 番剧名 (年份)/番剧名 (年份).mp4
        """
        renamed_files = []

        if scrape_mode == ScrapeMode.TV_SHOW:
            # 电视剧模式：创建 Season 01 目录
            if is_reorganize_directory:
                season_dir = series_dir / f"{SEASON_DIR_PREFIX}01"
                season_dir.mkdir(parents=True, exist_ok=True)
            else:
                season_dir = series_dir

            for entry in video_entries:
                video_path = Path(entry["file_path"])
                video_id = entry["video_id"]
                episode_num = episode_mapping.get(video_id, 0)

                if episode_num == 0:
                    continue

                if is_rename_file:
                    # 新文件名: S01E01.mp4
                    season_str = "S01"
                    episode_str = f"E{episode_num:02d}"
                    new_filename = f"{season_str}{episode_str}{video_path.suffix.lower()}"
                else:
                    new_filename = video_path.name

                new_path = season_dir / new_filename

                if video_path.exists() and video_path != new_path:
                    try:
                        # 移动文件
                        shutil.move(str(video_path), str(new_path))
                        renamed_files.append(f"{video_path.name} -> {new_path.relative_to(series_dir)}")
                        logger.info(f"文件重命名: {video_path.name} -> {new_path.relative_to(series_dir)}")
                    except Exception as e:
                        logger.error(f"文件重命名失败: {video_path} -> {new_path}: {e}")

        elif scrape_mode == ScrapeMode.MOVIE:
            # 电影模式：重命名为 番剧名 (年份).mp4
            for entry in video_entries:
                video_path = Path(entry["file_path"])
                video_id = entry["video_id"]

                # 尝试获取年份
                year_str = ""
                try:
                    video_detail = await self.video_service.get_video_detail(video_id)
                    if video_detail and hasattr(video_detail, "upload_date") and video_detail.upload_date:
                        if isinstance(video_detail.upload_date, datetime):
                            year_str = f" ({video_detail.upload_date.year})"
                        else:
                            year_str = f" ({str(video_detail.upload_date)[:4]})"
                except Exception:
                    pass

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
                    except Exception as e:
                        logger.error(f"电影文件重命名失败: {e}")

        return renamed_files

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
        episode_mapping = self._determine_episode_number(video_entries)

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
            for entry in video_entries:
                video_id = entry["video_id"]
                episode_num = episode_mapping.get(video_id, 0)
                if episode_num == 0:
                    continue
                meta = next((m for i, m in enumerate(metadata_list)
                              if video_entries[i]["video_id"] == video_id), None)
                episode_nfo = self.generate_episode_nfo(meta, 1, episode_num)
                season_str = f"S01"
                episode_str = f"E{episode_num:02d}"
                nfo_filename = f"{season_str}{episode_str}.nfo"
                preview.episode_nfos.append({
                    "filename": nfo_filename,
                    "content": episode_nfo
                })

                # 重命名映射
                original_name = Path(entry["file_path"]).name
                new_name = f"{season_str}{episode_str}.mp4"
                if original_name != new_name:
                    preview.rename_mapping.append({
                        "original": original_name,
                        "new": f"Season 01/{new_name}"
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
        episode_mapping: Dict[str, int]
    ) -> tuple:
        """生成电视剧模式的NFO和图片文件"""
        nfo_files = []
        image_files = []

        # 1. 生成 tvshow.nfo
        first_video_id = video_entries[0]["video_id"] if video_entries else ""
        tvshow_nfo_content = self.generate_tvshow_nfo(
            series_name, metadata_list, first_video_id
        )
        tvshow_nfo_path = series_dir / TVSHOW_NFO_FILENAME
        await self._write_nfo_file(tvshow_nfo_path, tvshow_nfo_content)
        nfo_files.append(str(tvshow_nfo_path))

        # 2. 生成 poster.jpg
        first_cover_url = ""
        for meta in metadata_list:
            if meta and hasattr(meta, "cover_url") and meta.cover_url:
                first_cover_url = meta.cover_url
                break

        poster_success = await self.generate_poster(series_dir, first_cover_url)
        if poster_success:
            image_files.append(str(series_dir / "poster.jpg"))

        # 3. 生成 fanart.jpg
        fanart_success = await self.generate_fanart(series_dir, first_cover_url)
        if fanart_success:
            image_files.append(str(series_dir / "fanart.jpg"))

        # 4. 生成各集NFO和缩略图
        # 确定Season目录（可能已经重组过）
        season_dir = series_dir / f"{SEASON_DIR_PREFIX}01"

        for i, entry in enumerate(video_entries):
            video_id = entry["video_id"]
            episode_num = episode_mapping.get(video_id, 0)
            if episode_num == 0:
                continue

            meta = metadata_list[i] if i < len(metadata_list) else None

            # 单集NFO
            episode_nfo_content = self.generate_episode_nfo(meta, 1, episode_num)
            season_str = f"S01"
            episode_str = f"E{episode_num:02d}"
            nfo_filename = f"{season_str}{episode_str}.nfo"

            # NFO文件放在Season目录（如果存在）或根目录
            nfo_save_dir = season_dir if season_dir.exists() else series_dir
            episode_nfo_path = nfo_save_dir / nfo_filename
            await self._write_nfo_file(episode_nfo_path, episode_nfo_content)
            nfo_files.append(str(episode_nfo_path))

            # 单集缩略图
            cover_url = ""
            if meta and hasattr(meta, "cover_url") and meta.cover_url:
                cover_url = meta.cover_url
            thumb_success = await self.generate_episode_thumb(
                nfo_save_dir, 1, episode_num, cover_url
            )
            if thumb_success:
                thumb_filename = f"{season_str}{episode_str}-thumb.jpg"
                image_files.append(str(nfo_save_dir / thumb_filename))

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
            image_files.append(str(series_dir / "poster.jpg"))

        # 生成 fanart.jpg
        fanart_success = await self.generate_fanart(series_dir, cover_url)
        if fanart_success:
            image_files.append(str(series_dir / "fanart.jpg"))

        return nfo_files, image_files

    def _scan_series_directory(self, series_dir: Path) -> List[Dict]:
        """
        扫描番剧目录，返回视频文件列表及解析出的 video_id

        支持两种目录结构：
        1. 扁平结构: 番剧名/video_id_subtitle.mp4
        2. Season结构: 番剧名/Season 01/S01E01.mp4
        """
        entries = []

        # 扫描根目录
        for f in series_dir.iterdir():
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                video_id = self._extract_video_id(f.stem)
                entries.append({
                    "file_path": str(f),
                    "filename": f.name,
                    "video_id": video_id,
                    "is_season_subdir": False
                })

        # 扫描 Season 子目录
        for sub in series_dir.iterdir():
            if sub.is_dir() and sub.name.startswith(SEASON_DIR_PREFIX):
                for f in sub.iterdir():
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                        video_id = self._extract_video_id(f.stem)
                        entries.append({
                            "file_path": str(f),
                            "filename": f.name,
                            "video_id": video_id,
                            "is_season_subdir": True
                        })

        return entries

    def _extract_video_id(self, filename_stem: str) -> str:
        """
        从文件名中提取 video_id

        格式1: {video_id}_{subtitle}  → video_id
        格式2: S01E01                → 空字符串（需要通过NFO查找）
        """
        # 尝试匹配 video_id_ 前缀
        match = re.match(r'^([a-zA-Z0-9]+?)_(.+)$', filename_stem)
        if match:
            candidate_id = match.group(1)
            if len(candidate_id) <= 20:
                return candidate_id

        # 尝试匹配 S01E01 格式
        if re.match(r'^S\d+E\d+$', filename_stem, re.IGNORECASE):
            return ""

        # 如果都不匹配，使用整个文件名作为ID
        return filename_stem

    def _determine_episode_number(self, video_entries: List[Dict]) -> Dict[str, int]:
        """
        确定每个视频的集号

        排序策略：
        1. 如果文件名中包含S01E01格式，直接提取
        2. 否则按文件创建时间排序，依次分配 1, 2, 3...
        """
        episode_mapping = {}
        regular_entries = []

        for entry in video_entries:
            filename = entry["filename"]
            # 尝试从S01E01格式提取集号
            match = re.search(r'S\d+E(\d+)', filename, re.IGNORECASE)
            if match:
                episode_num = int(match.group(1))
                episode_mapping[entry["video_id"]] = episode_num
            else:
                regular_entries.append(entry)

        # 对没有集号的条目按创建时间排序分配
        if regular_entries:
            # 按文件路径排序
            regular_entries.sort(key=lambda x: x["file_path"])
            # 找到已分配的最大集号
            max_episode = max(episode_mapping.values(), default=0)
            for i, entry in enumerate(regular_entries):
                episode_mapping[entry["video_id"]] = max_episode + i + 1

        return episode_mapping

    async def _fetch_metadata(self, video_entries: List[Dict]) -> List[Optional[Any]]:
        """从VideoService获取每个视频的元数据"""
        metadata_list = []
        for entry in video_entries:
            video_id = entry["video_id"]
            if not video_id:
                metadata_list.append(None)
                continue
            try:
                detail = await self.video_service.get_video_detail(video_id)
                metadata_list.append(detail)
            except Exception as e:
                logger.warning(f"获取视频元数据失败 video_id={video_id}: {e}")
                metadata_list.append(None)
        return metadata_list

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

        # 查找 video_id.jpg 格式的封面
        for f in series_dir.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpg", ".png", ".webp"):
                if f.stem and not f.name.startswith("S") and f.name != "fanart.jpg":
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

        绿联影视中心仅识别JPG格式！
        """
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 先下载到临时文件
            import tempfile
            import httpx

            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False
            ) as client:
                # 设置代理
                proxies = None
                if settings.USE_DOWNLOAD_PROXY and settings.DOWNLOAD_PROXY_URL:
                    proxies = settings.DOWNLOAD_PROXY_URL

                async with client.stream("GET", cover_url) as response:
                    if response.status_code != 200:
                        return False

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
                        async for chunk in response.aiter_bytes(8192):
                            tmp.write(chunk)
                        tmp_path = tmp.name

            # 转换为JPG
            try:
                if settings.SCRAPE_CONVERT_COVER_JPG:
                    success = self._convert_to_jpg(Path(tmp_path), save_path)
                else:
                    shutil.move(tmp_path, str(save_path))
                    success = True
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            return success

        except Exception as e:
            logger.error(f"下载封面失败: {e}")
            return False

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

                img.save(target_path, "JPEG", quality=95)
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

    async def _write_nfo_file(self, nfo_path: Path, content: str):
        """写入NFO文件"""
        try:
            nfo_path.parent.mkdir(parents=True, exist_ok=True)
            import aiofiles
            async with aiofiles.open(nfo_path, "w", encoding="utf-8") as f:
                await f.write(content)
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
        """生成格式化的XML字符串"""
        rough_string = ET.tostring(root, encoding="unicode", xml_declaration=False)
        try:
            parsed = minidom.parseString(rough_string)
            pretty = parsed.toprettyxml(indent="  ")
            # 移除minidom添加的额外XML声明
            lines = pretty.split("\n")
            if lines and lines[0].startswith("<?xml"):
                lines = lines[1:]
            content = NFO_XML_DECLARATION + "\n".join(lines)
            return content
        except Exception:
            return NFO_XML_DECLARATION + rough_string


# 创建刮削服务实例
scrape_service = ScrapeService()
