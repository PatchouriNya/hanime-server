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
                username TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS watch_later (
                username TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                videos TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS watch_history (
                username TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                duration TEXT DEFAULT '',
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                username TEXT PRIMARY KEY,
                settings TEXT DEFAULT '{}'
            )
            """)
            
            # 数据库迁移：为旧表添加 username 列
            await self._migrate_tables(conn)
            
            await conn.commit()
        logger.info("用户数据库初始化完成")

    async def _migrate_tables(self, conn):
        """数据库迁移 - 为旧表添加缺失的列"""
        # 检查 favorites 表是否有 username 列
        cursor = await conn.execute("PRAGMA table_info(favorites)")
        columns = [row[1] for row in await cursor.fetchall()]
        if columns and 'username' not in columns:
            logger.info("迁移 favorites 表：添加 username 列")
            # 旧表没有 username 列，需要重建表
            await conn.execute("ALTER TABLE favorites RENAME TO favorites_old")
            await conn.execute("""
            CREATE TABLE favorites (
                username TEXT NOT NULL DEFAULT 'admin',
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            # 将旧数据迁移到新表
            old_cols = ', '.join(columns)
            await conn.execute(f"INSERT INTO favorites (username, {old_cols}) SELECT 'admin', {old_cols} FROM favorites_old")
            await conn.execute("DROP TABLE favorites_old")

        # 检查 watch_later 表
        cursor = await conn.execute("PRAGMA table_info(watch_later)")
        columns = [row[1] for row in await cursor.fetchall()]
        if columns and 'username' not in columns:
            logger.info("迁移 watch_later 表：添加 username 列")
            await conn.execute("ALTER TABLE watch_later RENAME TO watch_later_old")
            await conn.execute("""
            CREATE TABLE watch_later (
                username TEXT NOT NULL DEFAULT 'admin',
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            old_cols = ', '.join(columns)
            await conn.execute(f"INSERT INTO watch_later (username, {old_cols}) SELECT 'admin', {old_cols} FROM watch_later_old")
            await conn.execute("DROP TABLE watch_later_old")

        # 检查 watch_history 表
        cursor = await conn.execute("PRAGMA table_info(watch_history)")
        columns = [row[1] for row in await cursor.fetchall()]
        if columns and 'username' not in columns:
            logger.info("迁移 watch_history 表：添加 username 列")
            await conn.execute("ALTER TABLE watch_history RENAME TO watch_history_old")
            await conn.execute("""
            CREATE TABLE watch_history (
                username TEXT NOT NULL DEFAULT 'admin',
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                cover_url TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                duration TEXT DEFAULT '',
                added_at TEXT NOT NULL,
                PRIMARY KEY (username, video_id)
            )
            """)
            old_cols = ', '.join(columns)
            await conn.execute(f"INSERT INTO watch_history (username, {old_cols}) SELECT 'admin', {old_cols} FROM watch_history_old")
            await conn.execute("DROP TABLE watch_history_old")

        # 检查 playlists 表
        cursor = await conn.execute("PRAGMA table_info(playlists)")
        columns = [row[1] for row in await cursor.fetchall()]
        if columns and 'username' not in columns:
            logger.info("迁移 playlists 表：添加 username 列")
            await conn.execute("ALTER TABLE playlists RENAME TO playlists_old")
            await conn.execute("""
            CREATE TABLE playlists (
                playlist_id TEXT PRIMARY KEY,
                username TEXT NOT NULL DEFAULT 'admin',
                name TEXT NOT NULL,
                videos TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            old_cols = ', '.join(columns)
            await conn.execute(f"INSERT INTO playlists (username, {old_cols}) SELECT 'admin', {old_cols} FROM playlists_old")
            await conn.execute("DROP TABLE playlists_old")
    
    async def add_favorite(self, username: str, video_id: str, title: str, cover_url: str) -> bool:
        """添加收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO favorites (username, video_id, title, cover_url, added_at)
                VALUES (?, ?, ?, ?, ?)
                """, (username, video_id, title, cover_url, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加收藏失败: {e}")
            return False
    
    async def remove_favorite(self, username: str, video_id: str) -> bool:
        """移除收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM favorites WHERE username = ? AND video_id = ?", (username, video_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除收藏失败: {e}")
            return False
    
    async def get_favorites(self, username: str) -> List[UserFavoriteItem]:
        """获取收藏列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM favorites WHERE username = ? ORDER BY added_at DESC", (username,))
                rows = await cursor.fetchall()
            
            return [UserFavoriteItem(
                video_id=row[1],
                title=row[2],
                cover_url=row[3],
                added_at=row[4]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取收藏列表失败: {e}")
            return []
    
    async def is_favorite(self, username: str, video_id: str) -> bool:
        """检查是否已收藏"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM favorites WHERE username = ? AND video_id = ?", (username, video_id))
                row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"检查收藏状态失败: {e}")
            return False
    
    async def add_watch_later(self, username: str, video_id: str, title: str, cover_url: str) -> bool:
        """添加稍后观看"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO watch_later (username, video_id, title, cover_url, added_at)
                VALUES (?, ?, ?, ?, ?)
                """, (username, video_id, title, cover_url, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加稍后观看失败: {e}")
            return False
    
    async def remove_watch_later(self, username: str, video_id: str) -> bool:
        """移除稍后观看"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_later WHERE username = ? AND video_id = ?", (username, video_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除稍后观看失败: {e}")
            return False
    
    async def get_watch_later(self, username: str) -> List[UserWatchLaterItem]:
        """获取稍后观看列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM watch_later WHERE username = ? ORDER BY added_at DESC", (username,))
                rows = await cursor.fetchall()
            
            return [UserWatchLaterItem(
                video_id=row[1],
                title=row[2],
                cover_url=row[3],
                added_at=row[4]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取稍后观看列表失败: {e}")
            return []
    
    async def is_watch_later(self, username: str, video_id: str) -> bool:
        """检查是否在稍后观看列表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM watch_later WHERE username = ? AND video_id = ?", (username, video_id))
                row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"检查稍后观看状态失败: {e}")
            return False
    
    async def create_playlist(self, username: str, name: str) -> Optional[UserPlaylist]:
        """创建播放清单"""
        try:
            playlist_id = str(int(time.time()))
            now = datetime.now().isoformat()
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT INTO playlists (playlist_id, username, name, videos, created_at, updated_at)
                VALUES (?, ?, ?, '[]', ?, ?)
                """, (playlist_id, username, name, now, now))
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
    
    async def delete_playlist(self, username: str, playlist_id: str) -> bool:
        """删除播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM playlists WHERE username = ? AND playlist_id = ?", (username, playlist_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除播放清单失败: {e}")
            return False
    
    async def get_playlists(self, username: str) -> List[UserPlaylist]:
        """获取所有播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM playlists WHERE username = ? ORDER BY created_at DESC", (username,))
                rows = await cursor.fetchall()
            
            playlists = []
            for row in rows:
                videos = json.loads(row[3]) if row[3] else []
                playlist_items = [PlaylistItem(**v) for v in videos]
                playlists.append(UserPlaylist(
                    playlist_id=row[0],
                    name=row[2],
                    videos=playlist_items,
                    created_at=row[4],
                    updated_at=row[5]
                ))
            return playlists
        except Exception as e:
            logger.error(f"获取播放清单列表失败: {e}")
            return []
    
    async def get_playlist(self, username: str, playlist_id: str) -> Optional[UserPlaylist]:
        """获取单个播放清单"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM playlists WHERE username = ? AND playlist_id = ?", (username, playlist_id))
                row = await cursor.fetchone()
            
            if not row:
                return None
            
            videos = json.loads(row[3]) if row[3] else []
            playlist_items = [PlaylistItem(**v) for v in videos]
            return UserPlaylist(
                playlist_id=row[0],
                name=row[2],
                videos=playlist_items,
                created_at=row[4],
                updated_at=row[5]
            )
        except Exception as e:
            logger.error(f"获取播放清单失败: {e}")
            return None
    
    async def add_video_to_playlist(self, username: str, playlist_id: str, video_id: str, title: str, cover_url: str) -> bool:
        """添加视频到播放清单"""
        try:
            playlist = await self.get_playlist(username, playlist_id)
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
                UPDATE playlists SET videos = ?, updated_at = ? WHERE username = ? AND playlist_id = ?
                """, (json.dumps([v.dict() for v in playlist.videos]), datetime.now().isoformat(), username, playlist_id))
                await conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"添加视频到播放清单失败: {e}")
            return False
    
    async def remove_video_from_playlist(self, username: str, playlist_id: str, video_id: str) -> bool:
        """从播放清单移除视频"""
        try:
            playlist = await self.get_playlist(username, playlist_id)
            if not playlist:
                return False
            
            playlist.videos = [v for v in playlist.videos if v.video_id != video_id]
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                UPDATE playlists SET videos = ?, updated_at = ? WHERE username = ? AND playlist_id = ?
                """, (json.dumps([v.dict() for v in playlist.videos]), datetime.now().isoformat(), username, playlist_id))
                await conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"从播放清单移除视频失败: {e}")
            return False
    
    async def update_playlist_name(self, username: str, playlist_id: str, name: str) -> bool:
        """更新播放清单名称"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                UPDATE playlists SET name = ?, updated_at = ? WHERE username = ? AND playlist_id = ?
                """, (name, datetime.now().isoformat(), username, playlist_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新播放清单名称失败: {e}")
            return False
    
    async def add_watch_history(self, username: str, video_id: str, title: str, cover_url: str, progress: int = 0, duration: str = "") -> bool:
        """添加观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO watch_history (username, video_id, title, cover_url, progress, duration, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, video_id, title, cover_url, progress, duration, datetime.now().isoformat()))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加观看历史失败: {e}")
            return False
    
    async def get_watch_history(self, username: str) -> List[WatchHistoryItem]:
        """获取观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT * FROM watch_history WHERE username = ? ORDER BY added_at DESC", (username,))
                rows = await cursor.fetchall()
            
            return [WatchHistoryItem(
                video_id=row[1],
                title=row[2],
                cover_url=row[3],
                progress=row[4],
                duration=row[5],
                added_at=row[6]
            ) for row in rows]
        except Exception as e:
            logger.error(f"获取观看历史失败: {e}")
            return []
    
    async def clear_watch_history(self, username: str) -> bool:
        """清空观看历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_history WHERE username = ?", (username,))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"清空观看历史失败: {e}")
            return False
    
    async def remove_watch_history(self, username: str, video_id: str) -> bool:
        """从观看历史移除单个视频"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM watch_history WHERE username = ? AND video_id = ?", (username, video_id))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"移除观看历史失败: {e}")
            return False
    
    async def get_user_settings(self, username: str) -> Dict[str, Any]:
        """获取用户设置"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute("SELECT settings FROM user_settings WHERE username = ?", (username,))
                row = await cursor.fetchone()
            
            if row and row[0]:
                return json.loads(row[0])
            return {}
        except Exception as e:
            logger.error(f"获取用户设置失败: {e}")
            return {}
    
    async def save_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """保存用户设置（合并模式：只更新传入的字段，不覆盖未传入的字段）"""
        try:
            # 读取现有设置，与传入的设置合并
            existing = await self.get_user_settings(username)
            existing.update(settings)
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                INSERT OR REPLACE INTO user_settings (username, settings)
                VALUES (?, ?)
                """, (username, json.dumps(existing)))
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存用户设置失败: {e}")
            return False


user_service = UserService()
