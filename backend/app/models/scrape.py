"""刮削相关模型定义

遵循 LibraryDream 命名规范：
- 枚举使用 UPPER_SNAKE_CASE
- 类名使用 PascalCase
- 字段名使用 snake_case
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ScrapeMode(str, Enum):
    """刮削模式枚举"""
    TV_SHOW = "tv_show"
    MOVIE = "movie"


class ScrapeConfig(BaseModel):
    """刮削配置模型"""
    scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW
    is_auto_scrape: bool = True
    is_rename_file: bool = True
    is_reorganize_directory: bool = True
    is_convert_cover_to_jpg: bool = True
    is_generate_fanart: bool = False


class ScrapeRequest(BaseModel):
    """刮削请求模型"""
    series_name: str = Field(..., description="番剧系列名（对应下载目录名）")
    scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW
    is_rename_file: bool = True
    is_reorganize_directory: bool = True


class BatchScrapeRequest(BaseModel):
    """批量刮削请求"""
    series_names: List[str] = Field(default_factory=list, description="空列表表示刮削所有")
    scrape_mode: ScrapeMode = ScrapeMode.TV_SHOW
    is_rename_file: bool = True
    is_reorganize_directory: bool = True


class ScrapeResult(BaseModel):
    """刮削结果模型"""
    series_name: str
    scrape_mode: ScrapeMode
    nfo_files: List[str] = Field(default_factory=list, description="生成的NFO文件列表")
    image_files: List[str] = Field(default_factory=list, description="生成的图片文件列表")
    renamed_files: List[str] = Field(default_factory=list, description="重命名的文件列表")
    is_success: bool = True
    error_message: Optional[str] = None


class ScrapableSeries(BaseModel):
    """可刮削的番剧系列信息"""
    series_name: str = Field(..., description="番剧目录名")
    video_count: int = Field(0, description="视频文件数量")
    has_nfo: bool = Field(False, description="是否已有NFO文件")
    has_poster: bool = Field(False, description="是否已有封面")
    video_files: List[str] = Field(default_factory=list, description="视频文件列表")


class NfoPreview(BaseModel):
    """NFO预览内容"""
    series_name: str
    scrape_mode: ScrapeMode
    tvshow_nfo: Optional[str] = None
    episode_nfos: List[dict] = Field(default_factory=list, description="单集NFO预览列表")
    movie_nfo: Optional[str] = None
    rename_mapping: List[dict] = Field(default_factory=list, description="文件重命名映射")
