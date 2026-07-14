import asyncio
import os
import time
import json
from typing import Dict, Optional, List, Set, Any
from datetime import datetime
import aiosqlite
from app.models.user import UserFavoriteItem, UserWatchLaterItem, UserPlaylist, PlaylistItem, WatchHistoryItem
from app.config import settings, logger


class UserService:
    """用户服务 - 管理收藏、稍后观看、播放清单、观看历史"""
    
    def __init__(self):
        self.db_path = settings.DB_PATH / "user.db"
        self._initialized = False
    
    async def initialize(self):
        """初始化数据库 - 在应用启动时调用"""
        if self._initialized:
            return
        await self.init_db()
        self._initialized = True
    
    async def init_db(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS watch_later (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                videos TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS watch_history (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                duration TEXT DEFAULT '',
                added_at TEXT NOT NULL
            )
            """)
            
            await conn.commit()
        logger.info("用户数据库初始化完成")
    
    async def add_favorite(self, video_id: str, title: str, cover_url: str) -> bool:
        """添加收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO favorites (video_id, title, cover_url, added_at)
                VALUES (?, ?, ?, ?)
                """, (video_id, title, cover_url, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加收藏失败: {e}")
            return False
    
    async def remove_favorite(self, video_id: str) -> bool:
        """移除收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM favorites WHERE video_id = ?", (video_id,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除收藏失败: {e}")
            return False
    
    async def get_favorites(self) -> List[UserFavoriteItem]:
        """获取收藏列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM favorites ORDER BY added_at DESC")
                rows = await cursor.fetchall()
            
            return [UserFavoriteItem(
                video_id=row[0],
                title=row[1],
                cover_url=row[2],
                added_at=row[3]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取收藏列表失败: {e}")
            return []
    
    async def is_favorite(self, video_id: str) -> bool:
        """检查是否已收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM favorites WHERE video_id = ?", (video_id,))
                row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"检查收藏状态失败: {e}")
            return False
    
    async def add_watch_later(self, video_id: str, title: str, cover_url: str) -> bool:
        """添加稍后观看"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO watch_later (video_id, title, cover_url, added_at)
                VALUES (?, ?, ?, ?)
                """, (video_id, title, cover_url, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加稍后观看失败: {e}")
            return False
    
    async def remove_watch_later(self, video_id: str) -> bool:
        """移除稍后观看"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_later WHERE video_id = ?", (video_id,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除稍后观看失败: {e}")
            return False
    
    async def get_watch_later(self) -> List[UserWatchLaterItem]:
        """获取稍后观看列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM watch_later ORDER BY added_at DESC")
                rows = await cursor.fetchall()
            
            return [UserWatchLaterItem(
                video_id=row[0],
                title=row[1],
                cover_url=row[2],
                added_at=row[3]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取稍后观看列表失败: {e}")
            return []
    
    async def is_watch_later(self, video_id: str) -> bool:
        """检查是否在稍后观看列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM watch_later WHERE video_id = ?", (video_id,))
                row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"检查稍后观看状态失败: {e}")
            return False
    
    async def create_playlist(self, name: str) -> Optional[UserPlaylist]:
        """创建播放清单"""
        try:
            playlist_id = str(int(time.time()))
            now = datetime.now().isoformat()
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT INTO playlists (playlist_id, name, videos, created_at, updated_at)
                VALUES (?, ?, '[]', ?, ?)
                """, (playlist_id, name, now, now))
                await conn.commit()
            
            return UserPlaylist(
                playlist_id=playlist_id,
                name=name,
                videos=[],
                created_at=now,
                updated_at=now
            )
        except Exception as e:
            logger.error(f"创建播放清单失败: {e}")
            return None
    
    async def delete_playlist(self, playlist_id: str) -> bool:
        """删除播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除播放清单失败: {e}")
            return False
    
    async def get_playlists(self) -> List[UserPlaylist]:
        """获取所有播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM playlists ORDER BY created_at DESC")
                rows = await cursor.fetchall()
            
            playlists = []
            for row in rows:
                videos = json.loads(row[2]) if row[2] else []
                playlist_items = [PlaylistItem(**v) for v in videos]
                playlists.append(UserPlaylist(
                    playlist_id=row[0],
                    name=row[1],
                    videos=playlist_items,
                    created_at=row[3],
                    updated_at=row[4]
                ))
            return playlists
        except Exception as e:
            logger.error(f"获取播放清单列表失败: {e}")
            return []
    
    async def get_playlist(self, playlist_id: str) -> Optional[UserPlaylist]:
        """获取单个播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,))
                row = await cursor.fetchone()
            
            if not row:
                return None
            
            videos = json.loads(row[2]) if row[2] else []
            playlist_items = [PlaylistItem(**v) for v in videos]
            return UserPlaylist(
                playlist_id=row[0],
                name=row[1],
                videos=playlist_items,
                created_at=row[3],
                updated_at=row[4]
            )
        except Exception as e:
            logger.error(f"获取播放清单失败: {e}")
            return None
    
    async def add_video_to_playlist(self, playlist_id: str, video_id: str, title: str, cover_url: str) -> bool:
        """添加视频到播放清单"""
        try:
            playlist = await self.get_playlist(playlist_id)
            if not playlist:
                return False
            
            existing_videos = {v.video_id for v in playlist.videos}
            if video_id in existing_videos:
                return True
            
            playlist.videos.append(PlaylistItem(
                video_id=video_id,
                title=title,
                cover_url=cover_url,
                added_at=datetime.now().isoformat()
            ))
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                UPDATE playlists SET videos = ?, updated_at = ? WHERE playlist_id = ?
                """, (json.dumps([v.dict() for v in playlist.videos]), datetime.now().isoformat(), playlist_id))
                await conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"添加视频到播放清单失败: {e}")
            return False
    
    async def remove_video_from_playlist(self, playlist_id: str, video_id: str) -> bool:
        """从播放清单移除视频"""
        try:
            playlist = await self.get_playlist(playlist_id)
            if not playlist:
                return False
            
            playlist.videos = [v for v in playlist.videos if v.video_id != video_id]
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                UPDATE playlists SET videos = ?, updated_at = ? WHERE playlist_id = ?
                """, (json.dumps([v.dict() for v in playlist.videos]), datetime.now().isoformat(), playlist_id))
                await conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"从播放清单移除视频失败: {e}")
            return False
    
    async def update_playlist_name(self, playlist_id: str, name: str) -> bool:
        """更新播放清单名称"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                UPDATE playlists SET name = ?, updated_at = ? WHERE playlist_id = ?
                """, (name, datetime.now().isoformat(), playlist_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新播放清单名称失败: {e}")
            return False
    
    async def add_watch_history(self, video_id: str, title: str, cover_url: str, progress: int = 0, duration: str = "") -> bool:
        """添加观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO watch_history (video_id, title, cover_url, progress, duration, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (video_id, title, cover_url, progress, duration, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加观看历史失败: {e}")
            return False
    
    async def get_watch_history(self) -> List[WatchHistoryItem]:
        """获取观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM watch_history ORDER BY added_at DESC")
                rows = await cursor.fetchall()
            
            return [WatchHistoryItem(
                video_id=row[0],
                title=row[1],
                cover_url=row[2],
                progress=row[3],
                duration=row[4],
                added_at=row[5]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取观看历史失败: {e}")
            return []
    
    async def clear_watch_history(self) -> bool:
        """清空观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_history")
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"清空观看历史失败: {e}")
            return False
    
    async def remove_watch_history(self, video_id: str) -> bool:
        """从观看历史移除单个视频"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_history WHERE video_id = ?", (video_id,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除观看历史失败: {e}")
            return False


user_service = UserService()
