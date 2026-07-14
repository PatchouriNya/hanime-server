from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class UserVideoItem(BaseModel):
    """用户视频项基础模型"""
    video_id: str
    title: str
    cover_url: str
    added_at: str


class UserFavoriteItem(UserVideoItem):
    """收藏视频项"""
    pass


class UserWatchLaterItem(UserVideoItem):
    """稍后观看视频项"""
    pass


class PlaylistItem(UserVideoItem):
    """播放清单视频项"""
    pass


class UserPlaylist(BaseModel):
    """用户播放清单"""
    playlist_id: str
    name: str
    videos: List[PlaylistItem] = []
    created_at: str
    updated_at: str


class WatchHistoryItem(UserVideoItem):
    """观看历史项"""
    progress: int = 0
    duration: str = ""


class FavoritesResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[UserFavoriteItem] = []


class WatchLaterResponse(BaseModel):
    """稍后观看列表响应"""
    watch_later: List[UserWatchLaterItem] = []


class PlaylistsResponse(BaseModel):
    """播放清单列表响应"""
    playlists: List[UserPlaylist] = []


class WatchHistoryResponse(BaseModel):
    """观看历史响应"""
    history: List[WatchHistoryItem] = []


class VideoActionResponse(BaseModel):
    """视频操作响应"""
    success: bool
    message: str
