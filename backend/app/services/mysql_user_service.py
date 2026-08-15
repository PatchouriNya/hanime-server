"""
MySQL 用户服务 — 管理收藏、稍后观看、播放清单、观看历史、用户设置
用于云数据库模式，支持多项目共用 ld_user 表
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any

import aiomysql
from passlib.hash import pbkdf2_sha256

from app.models.user import (
    UserFavoriteItem, UserWatchLaterItem, UserPlaylist,
    PlaylistItem, WatchHistoryItem
)
from app.config import settings, logger


class MySQLUserService:
    """MySQL 用户数据服务"""

    def __init__(self):
        self._pool: Optional[aiomysql.Pool] = None

    async def _get_pool(self) -> aiomysql.Pool:
        """获取或创建连接池"""
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=10,
            )
            logger.info(f"MySQL 连接池已创建: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
        return self._pool

    async def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            logger.info("MySQL 连接池已关闭")

    # ---- 用户认证相关 ----

    async def authenticate_user(self, username: str, password: str) -> tuple[bool, Optional[int]]:
        """验证用户凭据，返回 (是否成功, ld_user_id)"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, password_hash FROM ld_user WHERE username = %s AND status = 10 AND is_deleted = 0",
                        (username,)
                    )
                    row = await cursor.fetchone()
            if row is None:
                return False, None
            ld_user_id, password_hash = row
            if pbkdf2_sha256.verify(password, password_hash):
                return True, ld_user_id
            return False, None
        except Exception as e:
            logger.error(f"MySQL 验证用户失败: {e}")
            raise

    # ---- v4.0.0: 用户角色与管理（管理员功能） ----

    async def get_user_type(self, ld_user_id: int) -> Optional[int]:
        """获取用户角色（10=普通用户, 20=管理员）"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT user_type FROM ld_user WHERE id = %s", (ld_user_id,)
                    )
                    row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"MySQL 获取用户角色失败: {e}")
            return None

    async def get_user_type_by_username(self, username: str) -> Optional[int]:
        """按用户名获取用户角色"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT user_type FROM ld_user WHERE username = %s AND is_deleted = 0",
                        (username,)
                    )
                    row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"MySQL 获取用户角色失败: {e}")
            return None

    async def list_users(self) -> List[Dict[str, Any]]:
        """获取所有用户列表（管理员）"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, username, user_type, status, created_at FROM ld_user WHERE is_deleted = 0 ORDER BY created_at"
                    )
                    rows = await cursor.fetchall()
            return [
                {"id": r[0], "username": r[1], "user_type": r[2], "status": r[3],
                 "created_at": r[4].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(r[4], datetime) else str(r[4])}
                for r in rows
            ]
        except Exception as e:
            logger.error(f"MySQL 获取用户列表失败: {e}")
            return []

    async def create_user(self, username: str, password: str, user_type: int = 10) -> bool:
        """创建用户（管理员）"""
        try:
            password_hash = pbkdf2_sha256.hash(password)
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO ld_user (username, password_hash, user_type, status) VALUES (%s, %s, %s, 10)",
                        (username, password_hash, user_type)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 创建用户失败: {e}")
            return False

    async def delete_user(self, ld_user_id: int) -> bool:
        """软删除用户（管理员）"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE ld_user SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (ld_user_id,)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 删除用户失败: {e}")
            return False

    async def reset_user_password(self, ld_user_id: int, new_password: str) -> bool:
        """重置用户密码（管理员）"""
        try:
            new_hash = pbkdf2_sha256.hash(new_password)
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE ld_user SET password_hash = %s WHERE id = %s",
                        (new_hash, ld_user_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 重置用户密码失败: {e}")
            return False

    async def update_user_status(self, ld_user_id: int, user_status: int) -> bool:
        """更新用户状态（管理员）：10=正常, 20=禁用, 30=封禁"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE ld_user SET status = %s WHERE id = %s",
                        (user_status, ld_user_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 更新用户状态失败: {e}")
            return False

    async def update_user_type(self, ld_user_id: int, user_type: int) -> bool:
        """更新用户角色（管理员）：10=普通用户, 20=管理员"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE ld_user SET user_type = %s WHERE id = %s",
                        (user_type, ld_user_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 更新用户角色失败: {e}")
            return False

    async def get_user_id_by_username(self, username: str) -> Optional[int]:
        """按用户名获取用户ID"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id FROM ld_user WHERE username = %s AND is_deleted = 0",
                        (username,)
                    )
                    row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"MySQL 获取用户ID失败: {e}")
            return None

    async def change_password(self, ld_user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT password_hash FROM ld_user WHERE id = %s", (ld_user_id,)
                    )
                    row = await cursor.fetchone()
                if not row:
                    return False
                if not pbkdf2_sha256.verify(old_password, row[0]):
                    return False
                new_hash = pbkdf2_sha256.hash(new_password)
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE ld_user SET password_hash = %s WHERE id = %s",
                        (new_hash, ld_user_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 修改密码失败: {e}")
            return False

    async def get_or_create_user(self, username: str) -> Optional[int]:
        """获取用户ID，用户不存在则创建"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id FROM ld_user WHERE username = %s AND is_deleted = 0",
                        (username,)
                    )
                    row = await cursor.fetchone()
                if row:
                    return row[0]
                password_hash = pbkdf2_sha256.hash("666666")
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO ld_user (username, password_hash, user_type, status) VALUES (%s, %s, 10, 10)",
                        (username, password_hash)
                    )
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"MySQL 获取/创建用户失败: {e}")
            return None

    # ---- 收藏 ----

    async def add_favorite(self, ld_user_id: int, video_id: str, title: str, cover_url: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_favorite (ld_user_id, video_id, title, cover_url)
                           VALUES (%s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE title = VALUES(title), cover_url = VALUES(cover_url), created_at = CURRENT_TIMESTAMP""",
                        (ld_user_id, video_id, title, cover_url)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 添加收藏失败: {e}")
            return False

    async def remove_favorite(self, ld_user_id: int, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_favorite WHERE ld_user_id = %s AND video_id = %s",
                        (ld_user_id, video_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 移除收藏失败: {e}")
            return False

    async def get_favorites(self, ld_user_id: int) -> List[UserFavoriteItem]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT video_id, title, cover_url, created_at FROM hanime_user_favorite WHERE ld_user_id = %s ORDER BY created_at DESC",
                        (ld_user_id,)
                    )
                    rows = await cursor.fetchall()
            return [UserFavoriteItem(
                video_id=r[0], title=r[1], cover_url=r[2],
                added_at=r[3].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(r[3], datetime) else str(r[3])
            ) for r in rows]
        except Exception as e:
            logger.error(f"MySQL 获取收藏列表失败: {e}")
            return []

    async def is_favorite(self, ld_user_id: int, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM hanime_user_favorite WHERE ld_user_id = %s AND video_id = %s",
                        (ld_user_id, video_id)
                    )
                    row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"MySQL 检查收藏状态失败: {e}")
            return False

    # ---- 稍后观看 ----

    async def add_watch_later(self, ld_user_id: int, video_id: str, title: str, cover_url: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_watch_later (ld_user_id, video_id, title, cover_url)
                           VALUES (%s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE title = VALUES(title), cover_url = VALUES(cover_url), created_at = CURRENT_TIMESTAMP""",
                        (ld_user_id, video_id, title, cover_url)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 添加稍后观看失败: {e}")
            return False

    async def remove_watch_later(self, ld_user_id: int, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_watch_later WHERE ld_user_id = %s AND video_id = %s",
                        (ld_user_id, video_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 移除稍后观看失败: {e}")
            return False

    async def get_watch_later(self, ld_user_id: int) -> List[UserWatchLaterItem]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT video_id, title, cover_url, created_at FROM hanime_user_watch_later WHERE ld_user_id = %s ORDER BY created_at DESC",
                        (ld_user_id,)
                    )
                    rows = await cursor.fetchall()
            return [UserWatchLaterItem(
                video_id=r[0], title=r[1], cover_url=r[2],
                added_at=r[3].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(r[3], datetime) else str(r[3])
            ) for r in rows]
        except Exception as e:
            logger.error(f"MySQL 获取稍后观看列表失败: {e}")
            return []

    async def is_watch_later(self, ld_user_id: int, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM hanime_user_watch_later WHERE ld_user_id = %s AND video_id = %s",
                        (ld_user_id, video_id)
                    )
                    row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"MySQL 检查稍后观看状态失败: {e}")
            return False

    # ---- 播放清单 ----

    async def create_playlist(self, ld_user_id: int, name: str) -> Optional[UserPlaylist]:
        try:
            playlist_id = str(uuid.uuid4())[:12]
            now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO hanime_user_playlist (ld_user_id, playlist_id, name) VALUES (%s, %s, %s)",
                        (ld_user_id, playlist_id, name)
                    )
            return UserPlaylist(
                playlist_id=playlist_id, name=name, videos=[],
                created_at=now, updated_at=now
            )
        except Exception as e:
            logger.error(f"MySQL 创建播放清单失败: {e}")
            return None

    async def delete_playlist(self, ld_user_id: int, playlist_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_playlist WHERE ld_user_id = %s AND playlist_id = %s",
                        (ld_user_id, playlist_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 删除播放清单失败: {e}")
            return False

    async def get_playlists(self, ld_user_id: int) -> List[UserPlaylist]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT playlist_id, name, created_at, updated_at FROM hanime_user_playlist WHERE ld_user_id = %s ORDER BY created_at DESC",
                        (ld_user_id,)
                    )
                    playlist_rows = await cursor.fetchall()

            playlists = []
            for prow in playlist_rows:
                pid = prow[0]
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "SELECT video_id, title, cover_url, sort_order, created_at FROM hanime_user_playlist_video WHERE playlist_id = %s ORDER BY sort_order, created_at",
                            (pid,)
                        )
                        video_rows = await cursor.fetchall()
                videos = [PlaylistItem(
                    video_id=v[0], title=v[1], cover_url=v[2],
                    added_at=v[4].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(v[4], datetime) else str(v[4])
                ) for v in video_rows]
                playlists.append(UserPlaylist(
                    playlist_id=pid, name=prow[1], videos=videos,
                    created_at=prow[2].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(prow[2], datetime) else str(prow[2]),
                    updated_at=prow[3].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(prow[3], datetime) else str(prow[3]),
                ))
            return playlists
        except Exception as e:
            logger.error(f"MySQL 获取播放清单列表失败: {e}")
            return []

    async def get_playlist(self, ld_user_id: int, playlist_id: str) -> Optional[UserPlaylist]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT playlist_id, name, created_at, updated_at FROM hanime_user_playlist WHERE ld_user_id = %s AND playlist_id = %s",
                        (ld_user_id, playlist_id)
                    )
                    prow = await cursor.fetchone()
                if not prow:
                    return None
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT video_id, title, cover_url, sort_order, created_at FROM hanime_user_playlist_video WHERE playlist_id = %s ORDER BY sort_order, created_at",
                        (playlist_id,)
                    )
                    video_rows = await cursor.fetchall()
            videos = [PlaylistItem(
                video_id=v[0], title=v[1], cover_url=v[2],
                added_at=v[4].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(v[4], datetime) else str(v[4])
            ) for v in video_rows]
            return UserPlaylist(
                playlist_id=prow[0], name=prow[1], videos=videos,
                created_at=prow[2].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(prow[2], datetime) else str(prow[2]),
                updated_at=prow[3].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(prow[3], datetime) else str(prow[3]),
            )
        except Exception as e:
            logger.error(f"MySQL 获取播放清单失败: {e}")
            return None

    async def add_video_to_playlist(self, ld_user_id: int, playlist_id: str, video_id: str, title: str, cover_url: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_playlist_video (playlist_id, video_id, title, cover_url)
                           VALUES (%s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE title = VALUES(title), cover_url = VALUES(cover_url)""",
                        (playlist_id, video_id, title, cover_url)
                    )
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE hanime_user_playlist SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = %s",
                        (playlist_id,)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 添加视频到播放清单失败: {e}")
            return False

    async def remove_video_from_playlist(self, ld_user_id: int, playlist_id: str, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_playlist_video WHERE playlist_id = %s AND video_id = %s",
                        (playlist_id, video_id)
                    )
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE hanime_user_playlist SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = %s",
                        (playlist_id,)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 从播放清单移除视频失败: {e}")
            return False

    async def update_playlist_name(self, ld_user_id: int, playlist_id: str, name: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE hanime_user_playlist SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE ld_user_id = %s AND playlist_id = %s",
                        (name, ld_user_id, playlist_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 更新播放清单名称失败: {e}")
            return False

    async def move_video_between_playlists(self, ld_user_id: int, from_playlist_id: str, to_playlist_id: str, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT video_id, title, cover_url FROM hanime_user_playlist_video WHERE playlist_id = %s AND video_id = %s",
                        (from_playlist_id, video_id)
                    )
                    video = await cursor.fetchone()
                if not video:
                    return False
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_playlist_video WHERE playlist_id = %s AND video_id = %s",
                        (from_playlist_id, video_id)
                    )
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_playlist_video (playlist_id, video_id, title, cover_url)
                           VALUES (%s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE title = VALUES(title), cover_url = VALUES(cover_url)""",
                        (to_playlist_id, video[0], video[1], video[2])
                    )
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE hanime_user_playlist SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id IN (%s, %s)",
                        (from_playlist_id, to_playlist_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 移动视频失败: {e}")
            return False

    # ---- 观看历史 ----

    async def add_watch_history(self, ld_user_id: int, video_id: str, title: str, cover_url: str, progress: int = 0, duration: str = "") -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_watch_history (ld_user_id, video_id, title, cover_url, progress, duration)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE title = VALUES(title), cover_url = VALUES(cover_url),
                           progress = VALUES(progress), duration = VALUES(duration), watched_at = CURRENT_TIMESTAMP""",
                        (ld_user_id, video_id, title, cover_url, progress, duration)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 添加观看历史失败: {e}")
            return False

    async def get_watch_history(self, ld_user_id: int) -> List[WatchHistoryItem]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT video_id, title, cover_url, progress, duration, watched_at FROM hanime_user_watch_history WHERE ld_user_id = %s ORDER BY watched_at DESC",
                        (ld_user_id,)
                    )
                    rows = await cursor.fetchall()
            return [WatchHistoryItem(
                video_id=r[0], title=r[1], cover_url=r[2],
                progress=r[3], duration=r[4],
                added_at=r[5].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(r[5], datetime) else str(r[5])
            ) for r in rows]
        except Exception as e:
            logger.error(f"MySQL 获取观看历史失败: {e}")
            return []

    async def clear_watch_history(self, ld_user_id: int) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_watch_history WHERE ld_user_id = %s",
                        (ld_user_id,)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 清空观看历史失败: {e}")
            return False

    async def remove_watch_history(self, ld_user_id: int, video_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_watch_history WHERE ld_user_id = %s AND video_id = %s",
                        (ld_user_id, video_id)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 移除观看历史失败: {e}")
            return False

    # ---- 用户设置 ----

    async def get_user_settings(self, ld_user_id: int) -> Dict[str, Any]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT settings_data FROM hanime_user_setting WHERE ld_user_id = %s",
                        (ld_user_id,)
                    )
                    row = await cursor.fetchone()
            if row and row[0]:
                if isinstance(row[0], str):
                    return json.loads(row[0])
                return row[0]
            return {}
        except Exception as e:
            logger.error(f"MySQL 获取用户设置失败: {e}")
            return {}

    async def save_user_settings(self, ld_user_id: int, new_settings: Dict[str, Any]) -> bool:
        try:
            existing = await self.get_user_settings(ld_user_id)
            existing.update(new_settings)
            settings_json = json.dumps(existing)
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_setting (ld_user_id, settings_data)
                           VALUES (%s, %s)
                           ON DUPLICATE KEY UPDATE settings_data = VALUES(settings_data), updated_at = CURRENT_TIMESTAMP""",
                        (ld_user_id, settings_json)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 保存用户设置失败: {e}")
            return False

    # ---- 番剧追更订阅（v4.0.0） ----

    async def add_subscription(self, ld_user_id: int, series_name: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO hanime_user_subscription (ld_user_id, series_name)
                           VALUES (%s, %s)
                           ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP""",
                        (ld_user_id, series_name)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 添加订阅失败: {e}")
            return False

    async def remove_subscription(self, ld_user_id: int, series_name: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM hanime_user_subscription WHERE ld_user_id = %s AND series_name = %s",
                        (ld_user_id, series_name)
                    )
            return True
        except Exception as e:
            logger.error(f"MySQL 移除订阅失败: {e}")
            return False

    async def get_subscriptions(self, ld_user_id: int) -> List[str]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT series_name FROM hanime_user_subscription WHERE ld_user_id = %s ORDER BY created_at DESC",
                        (ld_user_id,)
                    )
                    rows = await cursor.fetchall()
            return [r[0] for r in rows]
        except Exception as e:
            logger.error(f"MySQL 获取订阅列表失败: {e}")
            return []

    async def is_subscribed(self, ld_user_id: int, series_name: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM hanime_user_subscription WHERE ld_user_id = %s AND series_name = %s",
                        (ld_user_id, series_name)
                    )
                    row = await cursor.fetchone()
            return row[0] > 0
        except Exception as e:
            logger.error(f"MySQL 检查订阅状态失败: {e}")
            return False


mysql_user_service = MySQLUserService()
