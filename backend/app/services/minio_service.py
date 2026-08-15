"""MinIO 对象存储服务

v4.0.0 新增：封面/头像等展示图片存储到 MinIO。
刮削生成的 NFO/海报等文件保持本地（绿联 NAS 影视中心依赖本地目录结构），
只有"展示用"图片（covers/{video_id}.jpg、avatars/...）会上传 MinIO。

启用条件：USE_MINIO=true（config.py 的 MINIO_* 配置）。
连接失败或未启用时自动降级为本地存储，不影响主流程。

遵循 LibraryDream 命名规范：
- 函数名 snake_case
- 常量 UPPER_SNAKE_CASE
- 类名 PascalCase
"""
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import settings, logger


class MinioService:
    """MinIO 对象存储客户端（模块级单例）"""

    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket_ready: bool = False

    @property
    def enabled(self) -> bool:
        """是否启用 MinIO"""
        return settings.USE_MINIO

    def _get_client(self) -> Optional[Minio]:
        """获取 MinIO 客户端（懒初始化）"""
        if not self.enabled:
            return None
        if self._client is None:
            try:
                self._client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=False,  # 内网部署默认 http
                )
                logger.info(f"MinIO 客户端已初始化: {settings.MINIO_ENDPOINT}")
            except Exception as e:
                logger.error(f"MinIO 客户端初始化失败: {e}")
                self._client = None
        return self._client

    async def ensure_bucket(self) -> bool:
        """确保 bucket 存在"""
        if not self.enabled or self._bucket_ready:
            return self._bucket_ready and self.enabled
        client = self._get_client()
        if not client:
            return False
        try:
            def _check():
                if not client.bucket_exists(settings.MINIO_BUCKET):
                    client.make_bucket(settings.MINIO_BUCKET)
                    return True
                return False

            created = await asyncio.to_thread(_check)
            if created:
                logger.info(f"MinIO bucket 已创建: {settings.MINIO_BUCKET}")
            self._bucket_ready = True
            return True
        except Exception as e:
            logger.warning(f"MinIO bucket 检查失败: {e}")
            return False

    @staticmethod
    def _object_name(prefix: str, name: str) -> str:
        """拼接对象名：{prefix}/{name}"""
        return f"{prefix}/{name}" if prefix else name

    async def upload_file(
        self,
        prefix: str,
        name: str,
        file_path: Path,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        上传本地文件到 MinIO

        :param prefix: 对象前缀（如 covers / avatars）
        :param name: 对象名（如 407019.jpg）
        :param file_path: 本地文件路径
        :param content_type: 内容类型
        :return: 对象名（如 covers/407019.jpg），失败返回 None
        """
        if not self.enabled:
            return None
        try:
            client = self._get_client()
            if not client:
                return None
            if not await self.ensure_bucket():
                return None
            object_name = self._object_name(prefix, name)

            def _upload():
                client.fput_object(
                    settings.MINIO_BUCKET, object_name, str(file_path),
                    content_type=content_type
                )

            await asyncio.to_thread(_upload)
            logger.debug(f"MinIO 上传成功: {object_name}")
            return object_name
        except Exception as e:
            logger.warning(f"MinIO 上传失败 ({prefix}/{name}): {e}")
            return None

    async def upload_bytes(
        self,
        prefix: str,
        name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """上传字节数据到 MinIO"""
        if not self.enabled:
            return None
        try:
            client = self._get_client()
            if not client:
                return None
            if not await self.ensure_bucket():
                return None
            object_name = self._object_name(prefix, name)

            def _upload():
                client.put_object(
                    settings.MINIO_BUCKET, object_name,
                    BytesIO(data), length=len(data),
                    content_type=content_type
                )

            await asyncio.to_thread(_upload)
            logger.debug(f"MinIO 上传成功(字节): {object_name}")
            return object_name
        except Exception as e:
            logger.warning(f"MinIO 上传失败 ({prefix}/{name}): {e}")
            return None

    async def get_object(self, prefix: str, name: str) -> Optional[bytes]:
        """从 MinIO 读取对象内容，不存在或失败返回 None"""
        if not self.enabled:
            return None
        try:
            client = self._get_client()
            if not client:
                return None
            object_name = self._object_name(prefix, name)

            def _get():
                response = client.get_object(settings.MINIO_BUCKET, object_name)
                try:
                    return response.read()
                finally:
                    response.close()
                    response.release_conn()

            return await asyncio.to_thread(_get)
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.warning(f"MinIO 读取失败 ({prefix}/{name}): {e}")
            return None
        except Exception as e:
            logger.warning(f"MinIO 读取失败 ({prefix}/{name}): {e}")
            return None

    async def exists(self, prefix: str, name: str) -> bool:
        """检查对象是否存在"""
        if not self.enabled:
            return False
        try:
            client = self._get_client()
            if not client:
                return False
            object_name = self._object_name(prefix, name)

            def _stat():
                client.stat_object(settings.MINIO_BUCKET, object_name)
                return True

            return await asyncio.to_thread(_stat)
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.warning(f"MinIO stat 失败: {e}")
            return False
        except Exception:
            return False

    async def delete_object(self, prefix: str, name: str) -> bool:
        """删除对象"""
        if not self.enabled:
            return False
        try:
            client = self._get_client()
            if not client:
                return False
            object_name = self._object_name(prefix, name)

            def _delete():
                client.remove_object(settings.MINIO_BUCKET, object_name)

            await asyncio.to_thread(_delete)
            return True
        except Exception as e:
            logger.warning(f"MinIO 删除失败 ({prefix}/{name}): {e}")
            return False

    async def close(self):
        """清理（MinIO 客户端无显式连接池，置空即可）"""
        self._client = None
        self._bucket_ready = False


# 全局单例
minio_service = MinioService()
