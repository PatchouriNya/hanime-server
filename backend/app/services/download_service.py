import asyncio
import os
import time
import math
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Set, Any
from fastapi import WebSocket
from datetime import datetime
import httpx
import aiosqlite
from app.models.download import DownloadStatus, DownloadSegment, DownloadProgress
from app.services.video_service import VideoService
from app.config import settings, logger
import aiofiles
import aiofiles.os
from urllib.parse import urlparse


class DownloadManager:
    """下载管理器"""
    
    def __init__(self):
        self.active_downloads: Dict[str, DownloadProgress] = {}
        self.websocket_connections: Set[WebSocket] = set()
        self.pause_events: Dict[str, asyncio.Event] = {}
        self.cancel_events: Dict[str, bool] = {}
        self.video_service = VideoService()
        
        # 配置参数
        # chunk_size: 每次从HTTP连接读取的数据块大小，影响内存使用和请求频率
        # 值越大，单次请求获取的数据越多，但占用内存也越多
        self.chunk_size = 1024 * 1024 * 4  # 4MB，调小以提高响应速度
        
        # buffer_size: 写入文件前在内存中累积的数据量
        # 较大的缓冲区可以减少磁盘I/O操作次数，提高性能
        self.buffer_size = 1024 * 1024 * 8   # 8MB
        
        # max_segments: 最大并发下载段数，影响并行度
        # 值越大并行度越高，但会增加系统和网络负载
        self.max_segments = 8  # 提高并发度
        
        # min_segment_size: 单个下载段的最小大小
        # 用于计算文件应该分成多少段，防止段过小导致性能下降
        # 文件总大小必须大于min_segment_size*2才会使用分段下载
        self.min_segment_size = 1024 * 1024 * 64  # 20MB，调小以适应更多文件使用分段下载
        
        # max_retries: 下载失败时的最大重试次数
        # 增加此值可以提高下载成功率，但可能导致长时间卡在失败的下载上
        self.max_retries = 5  # 增加重试次数提高可靠性
        
        # timeout: HTTP请求的超时时间(秒)
        # 较大的值适合网络不稳定的情况，较小的值可以更快检测到连接问题
        self.timeout = 10.0  # 适当减少超时时间
        
        # progress_update_interval: 更新下载进度的时间间隔(秒)
        # 值越小实时性越高，但会增加数据库操作和WebSocket通信频率
        self.progress_update_interval = 0.2  # 减少间隔提高实时性
        
        # 自适应参数
        self.bandwidth_samples = []  # 存储带宽样本用于自适应调整
        self.segment_adjust_threshold = 5  # 需要多少个样本才考虑调整段数
        self.connection_pool_size = 20  # HTTP连接池大小
        self.ws_batch_updates = True  # 启用WebSocket批量更新
        self.ws_throttle_interval = 0.1  # WebSocket节流间隔(秒)
        self.last_ws_update_time = {}  # 记录每个下载最后一次WS更新时间
        
        # 连接池
        self.http_clients = {}  # 存储基于域名的HTTP客户端连接池
        
        # 数据库路径
        self.db_path = settings.DB_PATH / "downloads.db"

        # 视频文件扩展名集合
        self.VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.wmv', '.flv', '.ts'}

    
    async def init_db(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                username TEXT NOT NULL,
                video_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                title TEXT,
                cover_url TEXT,
                url TEXT NOT NULL,
                total_size INTEGER,
                downloaded INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                PRIMARY KEY (username, video_id)
            )
            """)
            
            # 迁移：为旧表添加可能缺失的列
            migrations = [
                ("username", "TEXT NOT NULL DEFAULT 'admin'"),
                ("title", "TEXT"),
                ("cover_url", "TEXT"),
            ]
            for col_name, col_type in migrations:
                try:
                    await conn.execute(f"ALTER TABLE downloads ADD COLUMN {col_name} {col_type}")
                except:
                    pass  # 列已存在则忽略
            
            # 系列表：记录多个番剧合并为一个系列的关系
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_name TEXT NOT NULL,
                video_id TEXT NOT NULL,
                season_number INTEGER NOT NULL DEFAULT 1,
                episode_offset INTEGER NOT NULL DEFAULT 0,
                original_title TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(video_id)
            )
            """)

            await conn.commit()
    
    async def get_download_history(self, username: str) -> List[Dict[str, Any]]:
        """获取下载历史"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM downloads WHERE username = ? ORDER BY created_at DESC",
                (username,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def load_downloads(self):
        """从数据库加载下载历史"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM downloads WHERE status IN ('downloading', 'paused') ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    video_id = row['video_id']
                    # 安全地获取列值，处理可能不存在的列
                    retry_count = 0
                    if 'retry_count' in row.keys():
                        retry_count = row['retry_count']
                    
                    max_retries = 3
                    if 'max_retries' in row.keys():
                        max_retries = row['max_retries']
                    
                    self.active_downloads[video_id] = DownloadProgress(
                        video_id=video_id,
                        filename=row['filename'],
                        title=row['title'],
                        cover_url=row['cover_url'],
                        total_size=row['total_size'] or 0,
                        downloaded=row['downloaded'] or 0,
                        status=row['status'],
                        speed=0.0,
                        error_message=row['error_message'],
                        url=row['url'],
                        created_at=row['created_at'],
                        completed_at=row['completed_at'],
                        retry_count=retry_count,
                        max_retries=max_retries
                    )
                    # 恢复暂停状态
                    if row['status'] == DownloadStatus.PAUSED:
                        self.pause_events[video_id] = asyncio.Event()
                        self.pause_events[video_id].clear()
                    elif row['status'] == DownloadStatus.DOWNLOADING:
                        self.pause_events[video_id] = asyncio.Event()
                        self.pause_events[video_id].set()
                        # 重新启动下载
                        output_path = settings.DOWNLOAD_PATH / row['filename']
                        asyncio.create_task(
                            self.download_file(
                                video_id,
                                row['url'],
                                output_path,
                                resume=True
                            )
                        )

    async def broadcast_progress(self, video_id: str):
        """向所有连接的客户端广播下载进度，使用节流控制更新频率"""
        if video_id not in self.active_downloads:
            return
            
        # 检查是否需要更新（节流控制）
        current_time = asyncio.get_event_loop().time()
        last_update = self.last_ws_update_time.get(video_id, 0)
        if current_time - last_update < self.ws_throttle_interval and self.active_downloads[video_id].status == DownloadStatus.DOWNLOADING:
            # 如果间隔太小且不是关键状态变更，则跳过此次更新
            return
            
        # 更新最后更新时间
        self.last_ws_update_time[video_id] = current_time
            
        progress_data = self.active_downloads[video_id].dict()
        progress_data['speed'] = round(progress_data['speed'], 2)
        
        # 确保datetime对象被转换为ISO格式字符串
        if isinstance(progress_data['created_at'], datetime):
            progress_data['created_at'] = progress_data['created_at'].isoformat()
        if 'completed_at' in progress_data and isinstance(progress_data['completed_at'], datetime):
            progress_data['completed_at'] = progress_data['completed_at'].isoformat()
            
        message = json.dumps(progress_data)
        
        # 使用批处理发送以减少WebSocket压力
        failed_connections = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                failed_connections.append(websocket)
                logger.error(f"WebSocket发送失败: {str(e)}")
                
        # 移除失败的连接
        for ws in failed_connections:
            try:
                self.websocket_connections.remove(ws)
            except:
                pass

    async def update_db(self, video_id: str, **kwargs):
        """更新数据库中的下载记录"""
        await self.init_db()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE downloads SET {set_clause} WHERE video_id = ?",
                [*values, video_id]
            )
            await db.commit()
    
    async def download_file(self, video_id: str, url: str, output_path, resume: bool = False):
        """下载文件并更新进度"""
        if video_id not in self.active_downloads:
            raise Exception("无效的下载ID")

        # 创建暂停事件（如果不存在）
        if video_id not in self.pause_events:
            self.pause_events[video_id] = asyncio.Event()
            self.pause_events[video_id].set()
            
        # 初始化取消标志
        self.cancel_events[video_id] = False

        try:
            # 创建下载目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 获取复用的HTTP客户端
            client = await self.get_http_client(url)
            
            # 检查服务器是否支持范围请求
            try:
                # 使用较短的超时进行HEAD请求
                head_timeout = min(5.0, self.timeout)
                response = await client.head(url, timeout=head_timeout)
                accept_ranges = response.headers.get("accept-ranges", "").lower() == "bytes"
                total_size = int(response.headers.get("content-length", 0))
                    
                if total_size == 0:
                    # 如果HEAD请求没有返回文件大小，尝试GET请求
                    # 仅请求文件头部以获取大小信息
                    headers = {"Range": "bytes=0-8191"}  # 只请求前8KB
                    async with client.stream('GET', url, headers=headers) as response:
                        # 检查是否支持范围请求
                        if response.status_code == 206:
                            accept_ranges = True
                            content_range = response.headers.get("content-range", "")
                            if content_range and "/*" in content_range:
                                # 解析总大小
                                try:
                                    total_size = int(content_range.split("/")[1])
                                except ValueError:
                                    pass
                            
                        if total_size == 0:
                            # 如果仍然无法获取大小，则完整请求一次（但不下载）
                            async with client.stream('GET', url) as full_response:
                                total_size = int(full_response.headers.get("content-length", 0))
                                if total_size == 0:
                                    raise Exception("无法获取文件大小")
            except Exception as e:
                raise Exception(f"获取文件信息失败: {str(e)}")

            # 检查文件是否已存在且完整
            if os.path.exists(output_path) and not resume:
                file_size = os.path.getsize(output_path)
                if file_size == total_size:
                    self.active_downloads[video_id].status = DownloadStatus.COMPLETED
                    self.active_downloads[video_id].downloaded = file_size
                    self.active_downloads[video_id].total_size = file_size
                    await self.update_db(
                        video_id,
                        status=DownloadStatus.COMPLETED,
                        downloaded=file_size,
                        total_size=file_size,
                        completed_at=datetime.now()
                    )
                    await self.broadcast_progress(video_id)
                    return

            # 更新数据库中的总大小
            if not resume:
                await self.update_db(video_id, total_size=total_size)
            
            # 初始化或更新进度
            self.active_downloads[video_id].total_size = total_size
            self.active_downloads[video_id].status = DownloadStatus.DOWNLOADING
            
            # 动态确定是否使用分段下载及分段数量
            use_segmented_download = accept_ranges and total_size > self.min_segment_size * 2
            
            # 使用自适应分段算法
            optimal_segments = self.calculate_optimal_segments(total_size)
            logger.info(f"文件大小: {total_size} 字节, 自适应计算最佳段数: {optimal_segments}")
            
            if use_segmented_download:
                # 分段下载
                await self.segmented_download(video_id, url, output_path, total_size, resume, optimal_segments)
            else:
                # 单线程下载
                await self.simple_download(video_id, url, output_path, total_size, resume)
                
        except Exception as e:
            error_message = f"下载失败: {str(e)}"
            if video_id in self.active_downloads:
                self.active_downloads[video_id].status = DownloadStatus.ERROR
                self.active_downloads[video_id].error_message = error_message
                await self.update_db(
                    video_id,
                    status=DownloadStatus.ERROR,
                    error_message=error_message
                )
                await self.broadcast_progress(video_id)
            if os.path.exists(output_path) and not resume:
                try:
                    os.remove(output_path)
                except Exception as e:
                    logger.error(f"删除文件失败: {str(e)}")
        finally:
            # 清理暂停和取消事件
            if video_id in self.active_downloads and not (self.active_downloads[video_id].status == DownloadStatus.PAUSED):
                self.pause_events.pop(video_id, None)
                self.cancel_events.pop(video_id, None)
                
    def calculate_optimal_segments(self, file_size: int) -> int:
        """
        根据文件大小和历史带宽动态计算最佳分段数
        
        自适应算法策略:
        1. 文件越大，段数越多
        2. 根据以往下载速度动态调整
        3. 控制每个段的大小在合理范围内
        4. 考虑系统资源限制
        """
        # 默认基于文件大小的初始值
        base_segments = min(
            self.max_segments,  # 不超过最大限制
            max(1, file_size // (self.min_segment_size))  # 至少保证每段大小合理
        )
        
        # 如果有足够的带宽样本，考虑调整
        if len(self.bandwidth_samples) >= self.segment_adjust_threshold:
            avg_bandwidth = sum(self.bandwidth_samples) / len(self.bandwidth_samples)
            
            # 带宽较高时增加并发度，带宽较低时减少并发度
            # 以5MB/s为基准带宽
            base_bandwidth = 5 * 1024 * 1024  # 5MB/s
            bandwidth_factor = min(2.0, max(0.5, avg_bandwidth / base_bandwidth))
            
            adjusted_segments = round(base_segments * bandwidth_factor)
            return min(self.max_segments, max(1, adjusted_segments))
            
        return base_segments

    async def segmented_download(self, video_id: str, url: str, output_path, total_size: int, resume: bool = False, num_segments: int = None):
        """使用分段并发下载，支持自适应分段"""
        try:
            # 初始化时间和计数器
            last_update_time = asyncio.get_event_loop().time()
            last_downloaded = 0
            start_time = asyncio.get_event_loop().time()
            
            # 使用传入的段数或计算最佳段数
            if num_segments is None:
                num_segments = min(self.max_segments, max(1, total_size // self.min_segment_size))
                
            # 计算每个段的大小，使用自适应大小
            segment_size = math.ceil(total_size / num_segments)
            logger.info(f"文件大小: {total_size} 字节, 使用 {num_segments} 个下载段, 每段大小约 {segment_size} 字节")
            
            # 如果是恢复下载，检查哪些段已经完成
            if resume and hasattr(self.active_downloads[video_id], 'segments') and self.active_downloads[video_id].segments:
                segments = self.active_downloads[video_id].segments
                # 计算已下载量
                total_downloaded = sum(seg.downloaded for seg in segments)
                self.active_downloads[video_id].downloaded = total_downloaded
            else:
                # 创建新段，使用优化的段大小分配
                segments = []
                
                # 优化分段：前半部分段稍小，后半部分段略大，提高启动速度
                front_segments = max(1, num_segments // 3)  # 前1/3的段
                front_segment_size = segment_size * 0.8     # 前段略小
                back_segment_size = segment_size * 1.1      # 后段略大
                
                # 确保总大小保持不变
                total_front_size = front_segment_size * front_segments
                remaining_size = total_size - total_front_size
                back_segments = num_segments - front_segments
                
                if back_segments > 0:
                    back_segment_size = remaining_size / back_segments
                
                # 创建前部分段
                total_allocated = 0
                for i in range(front_segments):
                    start = total_allocated
                    allocated_size = int(front_segment_size)
                    if i == front_segments - 1:
                        # 最后一个前段可能需要调整大小
                        allocated_size = int(total_front_size - total_allocated)
                    end = min(start + allocated_size - 1, total_size - 1)
                    segments.append(DownloadSegment(start=start, end=end))
                    total_allocated += allocated_size
                
                # 创建后部分段
                for i in range(back_segments):
                    start = total_allocated
                    allocated_size = int(back_segment_size)
                    if i == back_segments - 1:
                        # 最后一段确保覆盖剩余所有字节
                        end = total_size - 1
                    else:
                        end = min(start + allocated_size - 1, total_size - 1)
                    segments.append(DownloadSegment(start=start, end=end))
                    total_allocated += allocated_size
                
                # 更新下载对象
                self.active_downloads[video_id].segments = segments
                
                # 创建空文件
                with open(output_path, "wb") as f:
                    f.seek(total_size - 1)
                    f.write(b'\0')
            
            # 创建下载任务，使用信号量控制并发
            semaphore = asyncio.Semaphore(num_segments)
            tasks = []
            for i, segment in enumerate(segments):
                if segment.status != "completed":
                    task = asyncio.create_task(
                        self.download_segment(
                            video_id, url, output_path, segment, i, semaphore
                        )
                    )
                    tasks.append(task)
            
            # 定时更新进度
            update_progress_task = asyncio.create_task(
                self.update_segmented_progress(
                    video_id, segments, last_update_time, last_downloaded
                )
            )
            
            # 等待所有下载任务完成
            await asyncio.gather(*tasks)
            
            # 取消更新进度任务
            update_progress_task.cancel()
            
            # 检查是否所有段都已完成
            all_completed = all(segment.status == "completed" for segment in segments)
            if all_completed:
                total_downloaded = total_size
                self.active_downloads[video_id].status = DownloadStatus.COMPLETED
                self.active_downloads[video_id].downloaded = total_downloaded
                completed_at = datetime.now()
                await self.update_db(
                    video_id,
                    status=DownloadStatus.COMPLETED,
                    downloaded=total_downloaded,
                    completed_at=completed_at
                )
                self.active_downloads[video_id].completed_at = completed_at
                
                # 计算带宽样本并存储
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time > 0:
                    bandwidth = total_size / elapsed_time  # bytes/second
                    # 保留最新的10个样本
                    self.bandwidth_samples.append(bandwidth)
                    if len(self.bandwidth_samples) > 10:
                        self.bandwidth_samples.pop(0)
                
                # 下载完成后自动刮削
                if settings.AUTO_SCRAPE_AFTER_DOWNLOAD:
                    try:
                        from app.services.scrape_service import scrape_service
                        asyncio.create_task(scrape_service.auto_scrape_after_download(video_id))
                    except Exception as e:
                        logger.warning(f"自动刮削触发失败: {e}")
                
            else:
                # 如果有段下载失败，整体下载失败
                self.active_downloads[video_id].status = DownloadStatus.ERROR
                self.active_downloads[video_id].error_message = "部分段下载失败"
                await self.update_db(
                    video_id,
                    status=DownloadStatus.ERROR,
                    error_message="部分段下载失败"
                )
            
            await self.broadcast_progress(video_id)
                
        except Exception as e:
            raise Exception(f"分段下载失败: {str(e)}")
    
    async def update_segmented_progress(self, video_id: str, segments: List[DownloadSegment], last_update_time, last_downloaded):
        """定期更新分段下载的进度"""
        try:
            while True:
                # 检查是否被取消
                if self.cancel_events.get(video_id):
                    return
                
                # 等待暂停事件
                await self.pause_events[video_id].wait()
                
                # 计算总下载量
                downloaded = sum(segment.downloaded for segment in segments)
                
                # 计算下载速度
                current_time = asyncio.get_event_loop().time()
                time_diff = current_time - last_update_time
                if time_diff >= self.progress_update_interval:
                    speed = (downloaded - last_downloaded) / time_diff
                    self.active_downloads[video_id].speed = speed
                    self.active_downloads[video_id].downloaded = downloaded
                    await self.update_db(video_id, downloaded=downloaded)
                    last_update_time = current_time
                    last_downloaded = downloaded
                    await self.broadcast_progress(video_id)
                
                await asyncio.sleep(self.progress_update_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"更新进度错误: {str(e)}")
    
    async def download_segment(self, video_id: str, url: str, output_path, segment: DownloadSegment, segment_index: int, semaphore: asyncio.Semaphore = None):
        """下载指定段，使用连接池和信号量控制并发"""
        max_retries = self.max_retries
        retries = 0
        backoff_time = 1  # 初始重试等待时间
        
        # 使用信号量控制并发量
        async with semaphore if semaphore else asyncio.nullcontext():
            while retries < max_retries:
                try:
                    # 检查是否被取消
                    if self.cancel_events.get(video_id):
                        return
                    
                    # 等待暂停事件
                    await self.pause_events[video_id].wait()
                    
                    # 计算实际起始位置
                    actual_start = segment.start + segment.downloaded
                    if actual_start > segment.end:
                        # 段已下载完成
                        segment.status = "completed"
                        return
                    
                    # 设置请求头
                    headers = {
                        "Range": f"bytes={actual_start}-{segment.end}",
                        "Connection": "keep-alive",  # 保持连接
                        "Accept-Encoding": "identity"  # 避免压缩导致的问题
                    }
                    
                    # 获取复用的HTTP客户端
                    client = await self.get_http_client(url)
                    
                    async with client.stream("GET", url, headers=headers) as response:
                        if response.status_code not in [200, 206]:
                            raise Exception(f"服务器返回错误状态码: {response.status_code}")
                        
                        segment.status = "downloading"
                        buffer = bytearray()
                        
                        # 使用aiofiles进行异步文件操作，提高性能
                        async with aiofiles.open(output_path, "r+b") as f:
                            await f.seek(actual_start)
                            
                            try:
                                async for chunk in response.aiter_bytes(self.chunk_size):
                                    # 检查是否被取消
                                    if self.cancel_events.get(video_id):
                                        return
                                    
                                    # 等待暂停事件
                                    await self.pause_events[video_id].wait()
                                    
                                    buffer.extend(chunk)
                                    if len(buffer) >= self.buffer_size:
                                        await f.write(buffer)
                                        segment.downloaded += len(buffer)
                                        buffer.clear()
                                
                                # 写入剩余buffer
                                if buffer:
                                    await f.write(buffer)
                                    segment.downloaded += len(buffer)
                                    
                            except asyncio.CancelledError:
                                # 处理取消请求
                                return
                        
                        # 段下载完成
                        segment.status = "completed"
                        logger.success(f"视频 {video_id} 段 {segment_index} 下载完成")
                        return
                except Exception as e:
                    retries += 1
                    # 使用指数退避策略进行重试
                    backoff_time = min(30, backoff_time * 1.5)  # 逐渐增加等待时间，但不超过30秒
                    logger.warning(f"视频 {video_id} 段 {segment_index} 下载失败 (尝试 {retries}/{max_retries}, 等待 {backoff_time:.1f}s): {str(e)}")
                    if retries >= max_retries:
                        segment.status = "error"
                        return
                    await asyncio.sleep(backoff_time)  # 使用指数退避等待
    
    async def simple_download(self, video_id: str, url: str, output_path, total_size: int, resume: bool = False):
        """使用单线程下载（用于不支持范围请求的服务器），优化性能和稳定性"""
        last_update_time = asyncio.get_event_loop().time()
        start_time = asyncio.get_event_loop().time()
        last_downloaded = 0
        downloaded = 0
        mode = "ab" if resume else "wb"
        
        if resume:
            downloaded = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            last_downloaded = downloaded
            
        await self.broadcast_progress(video_id)

        # 设置下载范围和优化的请求头
        headers = {
            "Connection": "keep-alive",
            "Accept-Encoding": "identity"  # 避免压缩导致的问题
        }
        
        if resume and downloaded > 0:
            headers["Range"] = f"bytes={downloaded}-"
        
        # 重试机制
        max_retries = self.max_retries
        retries = 0
        backoff_time = 1  # 初始重试等待时间
        
        while retries <= max_retries:
            try:
                # 获取复用的HTTP客户端
                client = await self.get_http_client(url)
                
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code not in [200, 206]:
                        raise Exception(f"服务器返回错误状态码: {response.status_code}")
                    
                    # 使用异步文件操作提高性能
                    async with aiofiles.open(output_path, mode) as f:
                        buffer = bytearray()
                        try:
                            async for chunk in response.aiter_bytes(self.chunk_size):
                                # 检查是否被取消
                                if self.cancel_events.get(video_id):
                                    logger.info(f"检测到取消操作: {video_id}")
                                    try:
                                        os.remove(output_path)
                                    except:
                                        pass
                                    self.active_downloads[video_id].status = DownloadStatus.CANCELLED
                                    await self.update_db(video_id, status=DownloadStatus.CANCELLED)
                                    await self.broadcast_progress(video_id)
                                    return

                                # 检查下载ID是否仍然有效
                                if video_id not in self.active_downloads:
                                    raise Exception("下载任务已失效")

                                # 等待暂停事件
                                await self.pause_events[video_id].wait()
                                
                                buffer.extend(chunk)
                                if len(buffer) >= self.buffer_size:
                                    await f.write(buffer)
                                    downloaded += len(buffer)
                                    buffer.clear()
                                
                                # 计算下载速度并使用节流更新进度
                                current_time = asyncio.get_event_loop().time()
                                time_diff = current_time - last_update_time
                                if time_diff >= self.progress_update_interval:
                                    speed = (downloaded - last_downloaded) / time_diff
                                    self.active_downloads[video_id].speed = speed
                                    self.active_downloads[video_id].downloaded = downloaded
                                    
                                    # 优化数据库更新频率 - 只在进度变化明显时更新数据库
                                    progress_percent = downloaded / total_size * 100 if total_size > 0 else 0
                                    if progress_percent - (last_downloaded / total_size * 100 if total_size > 0 else 0) >= 1.0:
                                        # 进度变化超过1%才更新数据库
                                        await self.update_db(video_id, downloaded=downloaded)
                                        
                                    last_update_time = current_time
                                    last_downloaded = downloaded
                                    await self.broadcast_progress(video_id)
                            
                            # 写入剩余buffer
                            if buffer:
                                await f.write(buffer)
                                downloaded += len(buffer)

                            # 最后一次更新进度
                            self.active_downloads[video_id].downloaded = downloaded
                            await self.update_db(video_id, downloaded=downloaded)
                            await self.broadcast_progress(video_id)

                        except Exception as chunk_error:
                            raise Exception(f"下载数据时出错: {str(chunk_error)}")
                    
                    # 验证下载是否完整
                    if total_size > 0 and downloaded != total_size:
                        raise Exception(f"下载不完整: 已下载 {downloaded} 字节，总大小 {total_size} 字节")
                    
                    # 完成下载
                    self.active_downloads[video_id].status = DownloadStatus.COMPLETED
                    self.active_downloads[video_id].downloaded = total_size
                    completed_at = datetime.now()
                    await self.update_db(
                        video_id,
                        status=DownloadStatus.COMPLETED,
                        downloaded=total_size,
                        completed_at=completed_at
                    )
                    self.active_downloads[video_id].completed_at = completed_at
                    
                    # 计算带宽样本并存储
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    if elapsed_time > 0:
                        bandwidth = total_size / elapsed_time  # bytes/second
                        # 保留最新的10个样本
                        self.bandwidth_samples.append(bandwidth)
                        if len(self.bandwidth_samples) > 10:
                            self.bandwidth_samples.pop(0)
                    
                    # 下载完成后自动刮削
                    if settings.AUTO_SCRAPE_AFTER_DOWNLOAD:
                        try:
                            from app.services.scrape_service import scrape_service
                            asyncio.create_task(scrape_service.auto_scrape_after_download(video_id))
                        except Exception as e:
                            logger.warning(f"自动刮削触发失败: {e}")
                    
                    await self.broadcast_progress(video_id)
                    
                    # 成功下载，不再重试
                    return
                    
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    raise Exception(f"单线程下载失败 (已重试 {retries-1} 次): {str(e)}")
                
                # 使用指数退避策略进行重试
                backoff_time = min(30, backoff_time * 1.5)
                logger.warning(f"视频 {video_id} 下载失败，等待 {backoff_time:.1f}s 后重试 ({retries}/{max_retries}): {str(e)}")
                await asyncio.sleep(backoff_time)

    async def pause_download(self, video_id: str):
        """暂停下载"""
        if video_id in self.pause_events:
            self.pause_events[video_id].clear()
            self.active_downloads[video_id].status = DownloadStatus.PAUSED
            await self.update_db(video_id, status=DownloadStatus.PAUSED)
            await self.broadcast_progress(video_id)
            return True
        return False

    async def resume_download(self, video_id: str):
        """继续下载"""
        if video_id in self.pause_events:
            self.pause_events[video_id].set()
            self.active_downloads[video_id].status = DownloadStatus.DOWNLOADING
            await self.update_db(video_id, status=DownloadStatus.DOWNLOADING)
            await self.broadcast_progress(video_id)
            return True
        return False

    async def retry_download(self, video_id: str):
        """重试下载"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM downloads WHERE video_id = ?",
                (video_id,)
            ) as cursor:
                download = await cursor.fetchone()
                if not download:
                    return False
                
                # 检查重试次数是否已达上限
                retry_count = download['retry_count'] + 1
                max_retries = download['max_retries'] if download['max_retries'] else 3
                
                if retry_count > max_retries:
                    # 更新错误信息
                    await db.execute(
                        "UPDATE downloads SET error_message = ? WHERE video_id = ?",
                        (f"已达到最大重试次数 ({max_retries})", video_id)
                    )
                    await db.commit()
                    if video_id in self.active_downloads:
                        self.active_downloads[video_id].error_message = f"已达到最大重试次数 ({max_retries})"
                    await self.broadcast_progress(video_id)
                    return False
                    
                # 更新下载状态为 downloading 并增加重试计数
                await db.execute(
                    "UPDATE downloads SET status = ?, error_message = NULL, retry_count = ? WHERE video_id = ?",
                    (DownloadStatus.DOWNLOADING, retry_count, video_id)
                )
                await db.commit()
                
                # 更新内存中的下载状态
                if video_id in self.active_downloads:
                    self.active_downloads[video_id].status = DownloadStatus.DOWNLOADING
                    self.active_downloads[video_id].error_message = None
                    self.active_downloads[video_id].retry_count = retry_count
                else:
                    # 如果active_downloads中不存在该ID，需要重新创建
                    self.active_downloads[video_id] = DownloadProgress(
                        video_id=video_id,
                        filename=download['filename'],
                        title=download['title'],
                        cover_url=download['cover_url'],
                        total_size=download['total_size'] or 0,
                        downloaded=download['downloaded'] or 0,
                        status=DownloadStatus.DOWNLOADING,
                        speed=0.0,
                        error_message=None,
                        url=download['url'],
                        created_at=download['created_at'],
                        completed_at=None,
                        retry_count=retry_count,
                        max_retries=max_retries
                    )
                    
                # 如果有暂停事件，设置它以继续下载
                if video_id in self.pause_events:
                    self.pause_events[video_id].set()
                else:
                    self.pause_events[video_id] = asyncio.Event()
                    self.pause_events[video_id].set()
                
                # 启动重试下载任务
                output_path = settings.DOWNLOAD_PATH / download["filename"]
                asyncio.create_task(
                    self.download_file(
                        video_id,
                        download["url"],
                        output_path,
                        resume=True
                    )
                )
                
                await self.broadcast_progress(video_id)
                return True

    async def cancel_download(self, video_id: str):
        """取消下载"""
        # 设置取消标志
        self.cancel_events[video_id] = True
        
        # 解除暂停以便取消操作能够进行
        if video_id in self.pause_events:
            self.pause_events[video_id].set()
            
        # 更新数据库中的状态
        await self.update_db(video_id, status=DownloadStatus.CANCELLED)
        
        # 更新内存中的状态
        if video_id in self.active_downloads:
            self.active_downloads[video_id].status = DownloadStatus.CANCELLED
            self.active_downloads[video_id].speed = 0  # 重置下载速度
            
            # 立即广播状态变化
            await self.broadcast_progress(video_id)
            
            # 等待一小段时间确保下载任务有机会响应取消事件
            await asyncio.sleep(0.5)
            
            # 检查任何可能仍在进行的下载线程是否需要强制终止
            # 此处可以添加更强力的终止策略
            
            return True
        
        return False

    async def check_existing_download(self, video_id: str, username: str) -> Optional[Dict[str, Any]]:
        """检查是否存在相同的下载"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM downloads WHERE username = ? AND video_id = ?",
                (username, video_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None

    async def delete_download(self, video_id: str, username: str, delete_files: bool = True) -> bool:
        """
        删除下载记录和文件

        :param video_id: 视频ID
        :param username: 用户名
        :param delete_files: 是否删除源文件（视频文件 + 刮削生成的 NFO 和图片）
                            True: 删除文件和记录（默认，向后兼容）
                            False: 只删除数据库记录，保留文件
        """
        try:
            await self.init_db()
            # 先检查下载是否处于活跃状态，如果是，先尝试取消
            if video_id in self.active_downloads and self.active_downloads[video_id].status in ['downloading', 'paused', 'pending']:
                logger.info(f"删除前自动取消下载: {video_id}")
                await self.cancel_download(video_id)
                # 等待一会儿确保取消操作完成
                await asyncio.sleep(1)

            async with aiosqlite.connect(self.db_path) as db:
                # 获取文件名
                async with db.execute(
                    "SELECT filename, status FROM downloads WHERE username = ? AND video_id = ?",
                    (username, video_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return False  # 记录不存在

                    filename = row[0]
                    status = row[1]

                    # 删除文件（仅当 delete_files=True 时）
                    if delete_files and filename:
                        await self._delete_video_and_scrape_files(filename, video_id)

                # 删除数据库记录
                await db.execute("DELETE FROM downloads WHERE username = ? AND video_id = ?", (username, video_id))
                await db.commit()
                logger.info(f"从数据库删除下载记录: {video_id} (delete_files={delete_files})")

                # 清理内存中的记录
                if video_id in self.active_downloads:
                    del self.active_downloads[video_id]
                if video_id in self.pause_events:
                    self.pause_events[video_id].set()  # 解除暂停
                    del self.pause_events[video_id]
                if video_id in self.cancel_events:
                    del self.cancel_events[video_id]
                # 清理速度计算数据
                if hasattr(self, 'speedSmoother') and self.speedSmoother:
                    self.speedSmoother.clearHistory(video_id)

                return True
        except Exception as e:
            logger.error(f"删除下载失败: {str(e)}")
            return False

    async def _find_nfo_by_video_id(self, series_dir, video_id: str) -> List:
        """
        递归搜索番剧目录，查找包含指定 video_id 的 NFO 文件

        通过匹配 NFO 中的 <uniqueid type="hanime" default="true">{video_id}</uniqueid> 来定位

        :param series_dir: 番剧根目录路径
        :param video_id: 视频ID
        :return: 匹配的 NFO 文件路径列表
        """
        matched_nfo_files = []
        uniqueid_pattern = f'<uniqueid type="hanime" default="true">{video_id}</uniqueid>'

        try:
            if not await aiofiles.os.path.exists(series_dir):
                return matched_nfo_files

            for root, dirs, files in os.walk(series_dir):
                for f in files:
                    if not f.lower().endswith('.nfo'):
                        continue
                    nfo_path = os.path.join(root, f)
                    try:
                        async with aiofiles.open(nfo_path, 'r', encoding='utf-8', errors='ignore') as nf:
                            content = await nf.read()
                            if uniqueid_pattern in content:
                                matched_nfo_files.append(nfo_path)
                    except Exception as e:
                        logger.warning(f"读取NFO文件失败: {nfo_path} - {e}")
        except Exception as e:
            logger.error(f"搜索NFO文件异常: {series_dir} - {e}")

        return matched_nfo_files

    async def _delete_video_and_scrape_files(self, filename: str, video_id: str) -> None:
        """
        删除视频文件及其关联的刮削文件

        删除策略：
        1. 先尝试删除原始路径的视频文件（未刮削的下载）
        2. 再通过 NFO 中的 uniqueid 查找刮削后重命名的文件
        3. 删除 NFO、对应的视频文件和缩略图
        4. 删除番剧根目录下的 video_id.jpg 封面
        5. 清理空目录

        :param filename: 数据库中存储的文件名（可能包含 series_name/ 前缀）
        :param video_id: 视频ID（用于查找 video_id.jpg 封面和 NFO 匹配）
        """
        if not filename:
            return

        video_extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.flv', '.ts'}

        try:
            file_path = settings.DOWNLOAD_PATH / filename
            series_name = filename.split('/')[0] if '/' in filename else None

            # 1. 先尝试删除原始路径的视频文件（未刮削的场景）
            try:
                if await aiofiles.os.path.exists(file_path):
                    await aiofiles.os.remove(file_path)
                    logger.info(f"删除原始视频文件成功: {file_path}")

                    # 删除与原始视频同名的 .nfo 和 .jpg
                    video_stem = file_path.stem
                    video_parent = file_path.parent
                    for ext in [".nfo", ".jpg"]:
                        scrape_file = video_parent / f"{video_stem}{ext}"
                        try:
                            if await aiofiles.os.path.exists(scrape_file):
                                await aiofiles.os.remove(scrape_file)
                                logger.info(f"删除刮削文件成功: {scrape_file}")
                        except Exception as e:
                            logger.warning(f"删除刮削文件失败: {scrape_file} - {e}")
            except Exception as file_error:
                logger.error(f"删除原始视频文件失败: {str(file_error)}")

            # 2. 通过 NFO 查找刮削后重命名的文件
            if series_name:
                series_dir = settings.DOWNLOAD_PATH / series_name
                nfo_files = await self._find_nfo_by_video_id(series_dir, video_id)

                for nfo_path in nfo_files:
                    nfo_path_obj = Path(nfo_path)
                    nfo_stem = nfo_path_obj.stem
                    nfo_parent = nfo_path_obj.parent

                    # 删除 NFO 文件
                    try:
                        if await aiofiles.os.path.exists(nfo_path):
                            await aiofiles.os.remove(nfo_path)
                            logger.info(f"删除NFO文件成功: {nfo_path}")
                    except Exception as e:
                        logger.warning(f"删除NFO文件失败: {nfo_path} - {e}")

                    # 删除与 NFO 同名的视频文件
                    for ext in video_extensions:
                        video_file = nfo_parent / f"{nfo_stem}{ext}"
                        try:
                            if await aiofiles.os.path.exists(video_file):
                                await aiofiles.os.remove(video_file)
                                logger.info(f"删除刮削后视频文件成功: {video_file}")
                        except Exception as e:
                            logger.warning(f"删除刮削后视频文件失败: {video_file} - {e}")

                    # 删除与 NFO 同名的缩略图 .jpg
                    thumb_file = nfo_parent / f"{nfo_stem}.jpg"
                    try:
                        if await aiofiles.os.path.exists(thumb_file):
                            await aiofiles.os.remove(thumb_file)
                            logger.info(f"删除单集缩略图成功: {thumb_file}")
                    except Exception as e:
                        logger.warning(f"删除单集缩略图失败: {thumb_file} - {e}")

                # 3. 删除番剧根目录下的 video_id.jpg 封面
                cover_file = series_dir / f"{video_id}.jpg"
                try:
                    if await aiofiles.os.path.exists(cover_file):
                        await aiofiles.os.remove(cover_file)
                        logger.info(f"删除封面文件成功: {cover_file}")
                except Exception as e:
                    logger.warning(f"删除封面文件失败: {cover_file} - {e}")

                # 4. 清理空目录
                await self._cleanup_empty_series_dir(series_dir)

        except Exception as e:
            logger.error(f"删除视频和刮削文件异常: {filename} - {e}")

    async def _cleanup_empty_series_dir(self, series_dir) -> None:
        """
        清理空的番剧目录（或只包含刮削文件但没有视频文件的目录）

        如果番剧目录下没有任何视频文件，则删除整个目录（包括所有 NFO 和图片）。
        因为没有视频文件，刮削文件也没有意义了。
        """
        try:
            if not await aiofiles.os.path.exists(series_dir):
                return

            # 检查目录及其所有子目录中是否还有视频文件
            video_extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.flv', '.ts'}
            has_video = False

            for root, dirs, files in os.walk(series_dir):
                for f in files:
                    if os.path.splitext(f)[1].lower() in video_extensions:
                        has_video = True
                        break
                if has_video:
                    break

            if not has_video:
                # 没有视频文件了，删除整个番剧目录
                try:
                    shutil.rmtree(series_dir)
                    logger.info(f"番剧目录已清空（无视频文件），删除整个目录: {series_dir}")
                except Exception as e:
                    logger.warning(f"删除空番剧目录失败: {series_dir} - {e}")

        except Exception as e:
            logger.error(f"清理空番剧目录异常: {series_dir} - {e}")

    async def batch_delete_downloads(
        self,
        video_ids: List[str],
        username: str,
        delete_files: bool = True
    ) -> Dict[str, Any]:
        """
        批量删除下载记录

        :param video_ids: 要删除的视频ID列表
        :param username: 用户名
        :param delete_files: 是否删除源文件（视频文件 + 刮削文件）
        :return: {"success_count": int, "failed_count": int, "failed_ids": List[str]}
        """
        success_count = 0
        failed_ids: List[str] = []

        for video_id in video_ids:
            try:
                success = await self.delete_download(video_id, username, delete_files)
                if success:
                    success_count += 1
                else:
                    failed_ids.append(video_id)
            except Exception as e:
                logger.error(f"批量删除单条失败: {video_id} - {e}")
                failed_ids.append(video_id)

        result = {
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "delete_files": delete_files
        }
        logger.info(f"批量删除完成: 成功 {success_count}, 失败 {len(failed_ids)}, 删除文件={delete_files}")
        return result

    async def merge_series_directories(
        self,
        series_name: str,
        items: List[Dict[str, Any]],
        username: str
    ) -> Dict[str, Any]:
        """
        合并多个番剧目录为一个系列目录

        流程：
        1. 创建系列根目录
        2. 对每个视频，将其从原始目录移动到系列目录的 Season N 子目录
        3. 更新数据库记录中的 filename 字段
        4. 保存系列关系到 series 表
        5. 清理空目录

        :param series_name: 合并后的系列根目录名
        :param items: [{"video_id": "13007", "season_number": 1}, {"video_id": "13405", "season_number": 2}]
        :param username: 用户名
        """
        await self.init_db()

        series_dir = settings.DOWNLOAD_PATH / series_name
        merged_items = []
        errors = []

        try:
            # 创建系列根目录
            series_dir.mkdir(parents=True, exist_ok=True)

            for item in items:
                video_id = item.get("video_id")
                season_number = item.get("season_number", 1)

                if not video_id:
                    continue

                # 查找该视频的下载记录
                download_info = await self.check_existing_download(video_id, username)
                if not download_info:
                    errors.append({"video_id": video_id, "error": "下载记录不存在"})
                    continue

                filename = download_info.get("filename", "")
                if not filename:
                    errors.append({"video_id": video_id, "error": "文件名为空"})
                    continue

                # 找到原始文件路径
                original_path = settings.DOWNLOAD_PATH / filename

                # 如果文件不在原始路径，查找刮削后的路径（通过NFO查找）
                actual_video_path = None
                related_files = []

                if not os.path.exists(original_path):
                    original_series_name = filename.split('/')[0] if '/' in filename else None
                    if original_series_name:
                        original_series_dir = settings.DOWNLOAD_PATH / original_series_name
                        nfo_files = await self._find_nfo_by_video_id(original_series_dir, video_id)
                        if nfo_files:
                            nfo_path = Path(nfo_files[0])
                            nfo_stem = nfo_path.stem
                            nfo_parent = nfo_path.parent
                            for ext in self.VIDEO_EXTENSIONS:
                                candidate = nfo_parent / f"{nfo_stem}{ext}"
                                if candidate.exists():
                                    actual_video_path = candidate
                                    break
                            # 收集相关的nfo和jpg
                            for nfo_f in nfo_files:
                                related_files.append(nfo_f)
                                nfo_p = Path(nfo_f)
                                thumb = nfo_p.parent / f"{nfo_p.stem}.jpg"
                                if thumb.exists():
                                    related_files.append(str(thumb))
                        else:
                            errors.append({"video_id": video_id, "error": f"找不到视频文件: {filename}"})
                            continue
                    else:
                        errors.append({"video_id": video_id, "error": f"找不到视频文件: {filename}"})
                        continue
                else:
                    actual_video_path = original_path

                if not actual_video_path or not actual_video_path.exists():
                    errors.append({"video_id": video_id, "error": f"视频文件不存在: {actual_video_path}"})
                    continue

                # 创建目标 Season 目录
                season_dir = series_dir / f"Season {season_number}"
                season_dir.mkdir(parents=True, exist_ok=True)

                # 计算集号：该 Season 下已有的视频数量 + 1
                existing_videos_in_season = [
                    f for f in season_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in self.VIDEO_EXTENSIONS
                ]
                episode_num = len(existing_videos_in_season) + 1

                # 新文件名：系列名 - S01E01 - 第 1 集.mp4
                safe_name = self._sanitize_filename(series_name)
                new_filename = f"{safe_name} - S{season_number:02d}E{episode_num:02d} - 第 {episode_num} 集{actual_video_path.suffix.lower()}"
                new_path = season_dir / new_filename

                # 移动视频文件
                try:
                    shutil.move(str(actual_video_path), str(new_path))
                    logger.info(f"合并系列: 移动视频 {actual_video_path} -> {new_path}")
                except Exception as e:
                    errors.append({"video_id": video_id, "error": f"移动视频文件, {str(e)}"})
                    continue

                # 移动相关文件（NFO、缩略图）
                for rel_file_path in related_files:
                    if isinstance(rel_file_path, str):
                        rel_file_path = Path(rel_file_path)
                    if rel_file_path.exists():
                        # NFO文件重命名
                        if rel_file_path.suffix.lower() == '.nfo':
                            new_nfo_name = f"{safe_name} - S{season_number:02d}E{episode_num:02d} - 第 {episode_num} 集.nfo"
                            new_nfo_path = season_dir / new_nfo_name
                            try:
                                shutil.move(str(rel_file_path), str(new_nfo_path))
                            except Exception as e:
                                logger.warning(f"移动NFO失败: {e}")
                        elif rel_file_path.suffix.lower() == '.jpg':
                            new_thumb_name = f"{safe_name} - S{season_number:02d}E{episode_num:02d} - 第 {episode_num} 集.jpg"
                            new_thumb_path = season_dir / new_thumb_name
                            try:
                                shutil.move(str(rel_file_path), str(new_thumb_path))
                            except Exception as e:
                                logger.warning(f"移动缩略图失败: {e}")

                # 移动封面文件
                original_series_name = filename.split('/')[0] if '/' in filename else None
                if original_series_name:
                    original_series_dir = settings.DOWNLOAD_PATH / original_series_name
                    cover_file = original_series_dir / f"{video_id}.jpg"
                    if cover_file.exists():
                        # 第一个视频的封面作为系列封面 poster.jpg
                        series_poster = series_dir / "poster.jpg"
                        if not series_poster.exists() or season_number == 1:
                            try:
                                shutil.copy2(str(cover_file), str(series_poster))
                                logger.info(f"复制封面为系列poster: {cover_file} -> {series_poster}")
                            except Exception as e:
                                logger.warning(f"复制封面失败: {e}")

                # 更新数据库记录
                new_relative_path = f"{series_name}/Season {season_number}/{new_filename}"
                try:
                    async with aiosqlite.connect(self.db_path) as conn:
                        await conn.execute(
                            "UPDATE downloads SET filename = ?, title = ? WHERE username = ? AND video_id = ?",
                            (new_relative_path, series_name, username, video_id)
                        )
                        await conn.commit()
                except Exception as e:
                    logger.error(f"更新下载记录失败: {video_id} - {e}")

                # 保存系列关系
                try:
                    async with aiosqlite.connect(self.db_path) as conn:
                        await conn.execute(
                            """INSERT OR REPLACE INTO series (series_name, video_id, season_number, episode_offset, original_title)
                            VALUES (?, ?, ?, ?, ?)""",
                            (series_name, video_id, season_number, (season_number - 1) * 10, download_info.get("title", ""))
                        )
                        await conn.commit()
                except Exception as e:
                    logger.error(f"保存系列关系失败: {video_id} - {e}")

                # 清理空目录
                if original_series_name:
                    original_series_dir = settings.DOWNLOAD_PATH / original_series_name
                    await self._cleanup_empty_series_dir(original_series_dir)

                merged_items.append({
                    "video_id": video_id,
                    "season_number": season_number,
                    "episode_number": episode_num,
                    "new_path": new_relative_path
                })

            return {
                "status": "success" if not errors else "partial",
                "series_name": series_name,
                "merged": merged_items,
                "errors": errors,
                "message": f"成功合并 {len(merged_items)} 个视频到系列「{series_name}」"
                           + (f"，{len(errors)} 个失败" if errors else "")
            }

        except Exception as e:
            logger.error(f"合并系列失败: {e}")
            return {
                "status": "error",
                "series_name": series_name,
                "merged": merged_items,
                "errors": errors + [{"error": str(e)}],
                "message": f"合并系列失败: {str(e)}"
            }

    async def start_download(self, video_id: str, username: str, force: bool = False):
        """
        启动下载
        :param video_id: 视频ID
        :param username: 用户名
        :param force: 是否强制重新下载已存在的视频
        """
        # 先检查是否有相同ID的下载记录
        existing_download = await self.check_existing_download(video_id, username)
        
        if existing_download and not force:
                return {
                    "status": "warning",
                "message": "视频已在下载列表中",
                    "existing_download": existing_download
                }
        elif existing_download and force:
            # 删除现有下载
            await self.delete_download(video_id, username)
            
        try:
            # 获取视频详情
            video_detail = await self.video_service.get_video_detail(video_id)
            if not video_detail:
                return {"status": "error", "message": "视频不存在或获取失败"}
            
            # 选择最佳的下载URL
            best_url = self._get_best_stream_url(video_detail.stream_urls)
            if not best_url:
                return {"status": "error", "message": "未找到有效的下载链接"}
            
            # 确定番剧系列名（目录名）—— 智能检测同系列已下载的番剧
            series_name, season_number, is_series_merge = await self._detect_series_directory(
                video_id, video_detail, username
            )
            logger.info(f"系列检测结果: video_id={video_id}, series_name={series_name}, season_number={season_number}, is_series_merge={is_series_merge}")

            # 优先使用副标题作为文件名，如果没有副标题则使用标题
            if video_detail.subtitle:
                filename = self._sanitize_filename(video_detail.subtitle)
            else:
                filename = self._sanitize_filename(video_detail.title)

            # 在下载目录下创建以番剧系列名命名的子目录
            series_dir = settings.DOWNLOAD_PATH / series_name
            series_dir.mkdir(parents=True, exist_ok=True)

            # 如果是系列合并，将文件放入对应的 Season 子目录
            if is_series_merge and season_number > 0:
                # 确保系列目录下的已有视频也被正确组织到 Season 子目录
                await self._ensure_series_season_structure(series_dir, series_name, username)

                season_dir = series_dir / f"Season {season_number}"
                season_dir.mkdir(parents=True, exist_ok=True)

                # === 集号识别策略（v3.3.4）===
                # 1. 优先从视频标题/副标题中提取真实集号
                #    例如 "第十一話"→11、"第4話"→4、"Episode 5"→5
                # 2. 收集 Season 目录中已存在的集号，避免冲突
                # 3. 如果真实集号未被占用，直接使用
                # 4. 如果已被占用（罕见：同集号不同视频），递增到下一个可用位置
                # 5. 如果无法从标题提取，按 Season 中已有视频数+1 顺序分配
                import re as _re
                used_episodes = set()
                for f in season_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in self.VIDEO_EXTENSIONS:
                        m = _re.search(r'S\d+E(\d+)', f.name, _re.IGNORECASE)
                        if m:
                            used_episodes.add(int(m.group(1)))

                real_episode = self._extract_real_episode_number(
                    video_detail.title or "",
                    video_detail.subtitle or ""
                )
                logger.info(f"集号识别: video_id={video_id}, "
                          f"title={video_detail.title}, subtitle={video_detail.subtitle}, "
                          f"识别集号={real_episode}, Season已有集号={sorted(used_episodes)}")

                if real_episode > 0:
                    episode_num = real_episode
                    # 冲突时递增到下一个可用位置
                    while episode_num in used_episodes:
                        episode_num += 1
                else:
                    # 无法识别真实集号，按 Season 中已有视频数+1 顺序分配
                    episode_num = max(used_episodes, default=0) + 1
                used_episodes.add(episode_num)

                # 文件名使用去掉年份后缀的基础名，保持与刮削服务一致
                base_name_for_filename = _re.sub(r'\s*\(\d{4}\)$', '', series_name).strip()
                safe_name = self._sanitize_filename(base_name_for_filename)
                filename = f"{series_name}/Season {season_number}/{safe_name} - S{season_number:02d}E{episode_num:02d} - 第 {episode_num} 集.mp4"
            else:
                filename = f"{series_name}/{video_id}_{filename}.mp4"

            # 创建下载记录
            file_path = settings.DOWNLOAD_PATH / filename
            
            # 预下载封面到番剧目录（不阻塞主流程）
            # video_detail.cover_url 已由 get_video_detail 优先处理为 /image/cover/ 格式
            async def _download_cover_async():
                await self.download_cover(video_id, video_detail.cover_url, series_dir, filename=video_id)

            asyncio.create_task(_download_cover_async())
            
            # 写入数据库（
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO downloads (username, video_id, title, filename, cover_url, url, status, total_size, downloaded, retry_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        username,
                        video_id, 
                        video_detail.title, 
                        filename, 
                        video_detail.cover_url, 
                        best_url, 
                        DownloadStatus.PENDING,
                        0,
                        0,
                        0
                    )
                )
                await conn.commit()
            
            # 创建下载进度对象
            self.active_downloads[video_id] = DownloadProgress(
                video_id=video_id,
                filename=filename,
                title=video_detail.title,
                cover_url=video_detail.cover_url,
                url=best_url,
                total_size=0,
                downloaded=0,
                status=DownloadStatus.PENDING,
                speed=0.0,
                created_at=datetime.now()
            )
            
            # 广播初始状态
            await self.broadcast_progress(video_id)
            
            # 启动下载任务
            asyncio.create_task(self.download_file(video_id, best_url, file_path))
            
            return {"status": "success", "message": "已开始下载"}
        except Exception as e:
            logger.error(f"启动下载失败: {str(e)}")
            return {"status": "error", "message": f"启动下载失败: {str(e)}"}

    def _get_best_stream_url(self, stream_urls):
        """获取最佳视频流URL"""
        if not stream_urls:
            return None
            
        # 优先选择高质量流
        quality_priority = {"1080p": 1, "720p": 2, "480p": 3, "360p": 4, "240p": 5}
        
        # 由于stream_urls是VideoStreamUrl对象列表，我们需要通过属性访问
        sorted_streams = sorted(
            stream_urls, 
            key=lambda x: quality_priority.get(x.quality.lower(), 999)
        )
        
        return sorted_streams[0].url if sorted_streams else None
    
    async def _ensure_series_season_structure(
        self,
        series_dir: Path,
        series_name: str,
        username: str
    ) -> None:
        """
        确保系列目录下的已有视频被正确组织到 Season 1 子目录

        一季多集策略（v3.3.3 回归标准电视剧结构）：
        - 所有根目录下的视频统一放入 Season 1
        - 文件名重命名为 S01E{NN} 格式，集号按顺序分配
        - 对齐绿联NAS标准电视剧识别格式（参考"未来日记 (2011)"结构）

        之前的"每集一季"策略（v3.2.7~v3.3.2）导致每季只有 E01，
        没有剧集顺序，NAS 无法识别为剧集，被当成独立电影拆分。

        :param series_dir: 系列根目录路径
        :param series_name: 系列名称
        :param username: 用户名
        """
        import re as _re
        import aiosqlite

        # 查找根目录下的视频文件（未整理到 Season 目录的）
        root_videos = []
        for f in sorted(series_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in self.VIDEO_EXTENSIONS:
                root_videos.append(f)

        if not root_videos:
            return  # 没有需要整理的视频

        # 收集 Season 1 中已存在的集号，避免冲突
        season_1_dir = series_dir / "Season 1"
        used_episodes = set()
        if season_1_dir.exists():
            for f in season_1_dir.iterdir():
                if f.is_file():
                    # 从文件名提取 S01E{NN} 的集号
                    m = _re.search(r'S\d+E(\d+)', f.name, _re.IGNORECASE)
                    if m:
                        used_episodes.add(int(m.group(1)))

        safe_name = self._sanitize_filename(series_name)
        # 去掉年份后缀
        safe_name = _re.sub(r'\s*\(\d{4}\)\s*$', '', safe_name).strip()

        # 创建 Season 1 目录
        season_1_dir.mkdir(parents=True, exist_ok=True)

        # === v3.3.4: 优先使用真实集号 ===
        # 1. 收集每个视频的 video_id 和数据库中存储的 title
        # 2. 对每个视频调用 _extract_real_episode_number 提取真实集号
        # 3. 真实集号冲突时递增；无法识别时回退到顺序分配
        video_titles: dict[str, str] = {}  # video_id -> title
        for vf in root_videos:
            m = _re.match(r'^(\d+)_', vf.name)
            if m:
                vid = m.group(1)
                video_titles[vf.name] = {"video_id": vid, "title": ""}

        # 一次性查询数据库，获取已记录的 title
        if video_titles:
            try:
                async with aiosqlite.connect(self.db_path) as conn:
                    conn.row_factory = aiosqlite.Row
                    ids_to_query = tuple(item["video_id"] for item in video_titles.values())
                    placeholders = ",".join("?" * len(ids_to_query))
                    async with conn.execute(
                        f"SELECT video_id, title FROM downloads WHERE video_id IN ({placeholders})",
                        ids_to_query
                    ) as cursor:
                        rows = await cursor.fetchall()
                    # 写回 video_titles
                    title_map = {row['video_id']: row['title'] or "" for row in rows}
                    for vf_name, info in video_titles.items():
                        info["title"] = title_map.get(info["video_id"], "")
            except Exception as e:
                logger.warning(f"查询数据库 video title 失败，将按顺序分配集号: {e}")

        # 为每个视频分配集号
        next_episode = max(used_episodes, default=0) + 1

        for video_file in root_videos:
            # 尝试从文件名提取 video_id（格式: {video_id}_{filename}.mp4）
            video_id = None
            m = _re.match(r'^(\d+)_', video_file.name)
            if m:
                video_id = m.group(1)

            # === 集号识别（v3.3.4）===
            # 优先从数据库中存储的标题中提取真实集号
            real_episode = 0
            if video_file.name in video_titles:
                stored_title = video_titles[video_file.name]["title"]
                if stored_title:
                    # 文件名中也含有原始标题信息，一起作为候选
                    # 提取 video_id_ 之后的部分作为标题候选
                    fn_stem = video_file.stem
                    title_from_filename = fn_stem.split("_", 1)[1] if "_" in fn_stem else fn_stem
                    real_episode = self._extract_real_episode_number(stored_title, title_from_filename)

            if real_episode > 0:
                episode_num = real_episode
                # 冲突时递增到下一个可用位置
                while episode_num in used_episodes:
                    episode_num += 1
            else:
                # 无法识别真实集号，按顺序分配
                while next_episode in used_episodes:
                    next_episode += 1
                episode_num = next_episode
            used_episodes.add(episode_num)
            next_episode = episode_num + 1

            logger.info(f"系列整理集号分配: {video_file.name} -> S01E{episode_num:02d} "
                       f"(真实集号识别={real_episode}, 已用集号={sorted(used_episodes)})")

            # 新文件名：系列名 - S01E{NN} - 第 {N} 集.mp4
            new_filename = (
                f"{safe_name} - S01E{episode_num:02d} - "
                f"第 {episode_num} 集{video_file.suffix.lower()}"
            )
            new_path = season_1_dir / new_filename

            try:
                shutil.move(str(video_file), str(new_path))
                logger.info(f"系列整理: {video_file.name} -> Season 1/{new_filename}")

                # 移动同名 NFO 和缩略图
                for ext in ['.nfo', '.jpg']:
                    old_assoc = video_file.parent / f"{video_file.stem}{ext}"
                    if old_assoc.exists():
                        new_assoc_name = (
                            f"{safe_name} - S01E{episode_num:02d} - "
                            f"第 {episode_num} 集{ext}"
                        )
                        new_assoc = season_1_dir / new_assoc_name
                        try:
                            shutil.move(str(old_assoc), str(new_assoc))
                        except Exception as e:
                            logger.warning(f"移动关联文件失败: {old_assoc} - {e}")

                # 更新数据库记录
                new_relative = f"{series_name}/Season 1/{new_filename}"
                async with aiosqlite.connect(self.db_path) as conn:
                    old_relative = f"{series_name}/{video_file.name}"
                    await conn.execute(
                        "UPDATE downloads SET filename = ? WHERE username = ? AND filename = ?",
                        (new_relative, username, old_relative)
                    )
                    await conn.execute(
                        "UPDATE downloads SET filename = ? WHERE username = ? AND filename LIKE ?",
                        (new_relative, username, f"{series_name}/{video_file.name}")
                    )
                    await conn.commit()

            except Exception as e:
                logger.error(f"系列整理失败: {video_file} -> {new_path}: {e}")

    async def _detect_series_directory(
        self,
        video_id: str,
        video_detail: Any,
        username: str
    ) -> tuple:
        """
        智能检测同系列已下载的番剧，返回正确的目录名和季号

        逻辑：
        1. 检查源站的 series_videos 信息
        2. 如果 series_videos 为空，从 basic_related_videos 中通过标题相似度识别同系列
        3. 遍历已下载目录，查找同系列视频所在的目录
        4. 如果找到，返回该系列目录名和计算出的季号
        5. 如果没找到，使用系列名（去掉编号后缀）作为目录名

        :return: (series_name, season_number, is_series_merge)
        """
        import re as _re

        series_videos = getattr(video_detail, 'series_videos', None) or []
        basic_related = getattr(video_detail, 'basic_related_videos', None) or []
        current_title = video_detail.title
        # 优先使用副标题（中文），因为格式更规范，更容易提取系列名
        # 例如：subtitle="欢迎光临！水龙敬乐园 1" 比 title="おいでよ！水龍敬ランド ＃1 ..." 更容易匹配
        current_subtitle = getattr(video_detail, 'subtitle', None) or ''
        name_source = current_subtitle if current_subtitle else current_title

        # 从标题中提取集号作为季号（每集一季策略）
        # 文字标签到季号的语义映射（统一处理上卷/下卷/前篇/后篇等非数字标签）
        _LABEL_TO_SEASON_NUMBER = {
            # 上/前 系列 → 1
            '上卷': 1, '上巻': 1, '前篇': 1, '前編': 1, '上篇': 1,
            # 中系列 → 2
            '中卷': 2, '中巻': 2, '中篇': 2, '中編': 2,
            # 下/后系列 → 3
            '下卷': 3, '下巻': 3, '後篇': 3, '後編': 3, '下篇': 3,
            '后篇': 3, '后編': 3, '下编': 3,
            # 番外/特典 → 99（特殊类，会触发冲突递增）
            'OVA': 99, '特典': 99, '番外': 99, '特別': 99, '特别': 99,
        }

        def _extract_episode_number_from_title(title: str) -> int:
            """
            从标题中提取集号作为季号，支持数字和文字标签
            未找到返回 0（由调用方按下载顺序分配）

            支持的格式：
            - 末尾数字：援助交配 10 → 10
            - 第N期/章/部：第2期 → 2
            - Season N：Season 2 → 2
            - 罗马数字：第Ⅱ → 2
            - 文字标签：上卷 → 1, 中卷 → 2, 下卷 → 3, OVA → 99
            """
            if not title:
                return 0
            title_stripped = title.strip()
            # 1. 匹配末尾的数字（如"援助交配 10"→10, "某番剧 2"→2）
            m = _re.search(r'(\d+)\s*$', title_stripped)
            if m:
                return int(m.group(1))
            # 2. 匹配 "第2期"、"第2章"、"第2部" 等
            m = _re.search(r'第\s*(\d+)\s*[期章部]', title)
            if m:
                return int(m.group(1))
            # 3. 匹配 "Season 2"、"Season2"
            m = _re.search(r'[Ss]eason\s*(\d+)', title)
            if m:
                return int(m.group(1))
            # 4. 匹配罗马数字 "第Ⅱ"、"第III"
            roman_map = {'Ⅰ': 1, 'Ⅱ': 2, 'Ⅲ': 3, 'IV': 4, 'Ⅴ': 5,
                         'I': 1, 'II': 2, 'III': 3}
            m = _re.search(r'第\s*([ⅠⅡⅢIVⅤI]{1,3})\s*$', title)
            if m:
                roman = m.group(1)
                if roman in roman_map:
                    return roman_map[roman]
            # 5. 匹配文字标签（上卷/下卷/前篇/后篇/OVA 等）
            # 按标签长度降序匹配，避免"下卷"被"卷"误匹配
            for label in sorted(_LABEL_TO_SEASON_NUMBER.keys(), key=len, reverse=True):
                if label in title:
                    return _LABEL_TO_SEASON_NUMBER[label]
            return 0

        # 提取系列名（去掉编号后缀）
        def _extract_series_base(title: str) -> str:
            """
            从标题中提取系列基础名

            处理两类编号：
            A. 末尾后缀：＃1、第2期、Season 2、2、上卷/前編/OVA 等
            B. 标题中间的集号标记："第十一話"、"第2話"、"＃11" 等
               （这些标记虽然不在末尾，但若不剥离会导致同一系列不同集
               被识别为不同系列基础名）

            示例：
              "○○交配 第一話 毎日お世話してくれる彼女はエルフのお姫様" → "○○交配 毎日お世話してくれる彼女はエルフのお姫様"
              "○○交配 第十一話 毎日お世話してくれる彼女はエルフのお姫様 前編" → "○○交配 毎日お世話してくれる彼女はエルフのお姫様"
              "援助交配 10" → "援助交配"
              "不潔之星・赤" → "不潔之星"
            """
            if not title:
                return title

            # 先去除 [中文字幕] 等末尾方括号注释，避免影响后续匹配
            result = _re.sub(r'\s*\[[^\]]*\]\s*$', '', title).strip()

            patterns = [
                # B 类：标题中间的集号标记（必须在末尾处理之前）
                # 集号 + 后面跟随的其他描述（如"前編"、"中文字幕"等）
                # 注意：要匹配"第十一話 毎日お世話" 这种中间标记，且不消耗后面的描述文字
                # 用一个 lookbehind 替换更安全：替换"第N話/话/期/章/部/卷/篇/編 + 后续空格"
                r'第\s*[零〇一二三四五六七八九十两\d]+\s*[話话期章部卷篇編]\s*',

                # A 类：末尾后缀（原逻辑保留）
                # 注意：Season N 必须放在 \d+$ 之前，否则 \d+$ 会先匹配掉末尾的数字
                r'\s*[＃#]\s*\d+.*$',                   # ＃1 はじめての... -> (去掉＃及之后所有内容)
                r'[・\s][赤青黒白紅緑黄紫]$',           # 不潔之星・赤 -> 不潔之星
                r'\s*[第ⅠⅡⅢ]\s*$',                     # 某番剧 第Ⅱ -> 某番剧
                r'\s*Season\s*\d+$',                     # 某番剧 Season 2 -> 某番剧
                r'\s*第\d+[期章部話]$',                   # 某番剧 第2期 -> 某番剧
                r'[・\-]\s*\d+$',                        # 某番剧・2 -> 某番剧
                r'\s*\d+$',                              # 某番剧 2 -> 某番剧（放在最后，避免误吞 Season 2 的数字）
                # 文字标签后缀（上卷/下卷/前篇/后篇/OVA 等）
                r'\s*(上卷|上巻|前篇|前編|上篇)$',
                r'\s*(中卷|中巻|中篇|中編)$',
                r'\s*(下卷|下巻|後篇|後編|下篇|后篇|后編|下编)$',
                r'\s*(OVA|特典|番外|特別|特别)$',
            ]
            for pattern in patterns:
                new_result = _re.sub(pattern, '', result, flags=_re.IGNORECASE)
                if new_result != result and len(new_result) >= 2:
                    result = new_result
            # 清理多余空格（中间集号剥离后会留下双空格）
            result = _re.sub(r'\s{2,}', ' ', result).strip()
            return result

        base_series_name = _extract_series_base(name_source)
        default_series_name = self._sanitize_filename(base_series_name)
        logger.info(f"系列检测: video_id={video_id}, name_source={name_source}, base_series_name={base_series_name}, default_series_name={default_series_name}")
        logger.info(f"系列检测: series_videos={len(series_videos)}, basic_related={len(basic_related)}")

        # 收集所有同系列视频（从 series_videos 或 basic_related_videos）
        detected_series_videos = []
        if series_videos:
            # 源站直接提供了 series_videos
            for sv in series_videos:
                detected_series_videos.append({
                    "video_id": sv.video_id,
                    "title": sv.title
                })
        else:
            # 源站没有提供 series_videos，从 basic_related_videos 中通过标题相似度识别
            # 策略：将相关视频的标题转为简体中文后，提取基础名与当前视频的基础名比较
            from app.utils.chinese_converter import to_simplified
            base_series_name_simplified = to_simplified(base_series_name)
            for rv in basic_related:
                rv_title = getattr(rv, 'title', '') or ''
                # 将相关视频标题也转为简体中文后提取基础名
                rv_title_simplified = to_simplified(rv_title)
                rv_base = _extract_series_base(rv_title_simplified)
                if rv_base and rv_base == base_series_name_simplified and rv.video_id != video_id:
                    detected_series_videos.append({
                        "video_id": rv.video_id,
                        "title": rv_title
                    })
                    logger.info(f"系列检测: 从相关视频中发现同系列: video_id={rv.video_id}, title={rv_title}, rv_base={rv_base}")

        logger.info(f"系列检测: 检测到同系列视频 {len(detected_series_videos)} 个")

        # 辅助函数：在下载目录中查找匹配的系列目录
        # 刮削服务可能会将目录重命名为 "番剧名 (年份)" 格式
        def _find_series_dir_on_disk(series_base_name: str) -> Optional[Path]:
            """
            在下载目录中查找系列目录，支持以下格式：
            1. 精确匹配：series_base_name
            2. 带年份后缀：series_base_name (YYYY)
            """
            # 精确匹配
            exact_dir = settings.DOWNLOAD_PATH / series_base_name
            if exact_dir.exists() and exact_dir.is_dir():
                return exact_dir
            # 带年份后缀匹配：查找 "series_base_name (YYYY)" 格式的目录
            for d in settings.DOWNLOAD_PATH.iterdir():
                if d.is_dir():
                    # 匹配 "番剧名 (2026)" 格式
                    match = _re.match(r'^(.+?)\s*\(\d{4}\)$', d.name)
                    if match and match.group(1).strip() == series_base_name:
                        return d
            return None

        # 如果没有检测到任何同系列视频，检查是否已有同系列目录存在
        if not detected_series_videos:
            existing_dir = _find_series_dir_on_disk(default_series_name)
            if existing_dir:
                # 检查该目录是否包含 Season 子目录（说明之前已经有合并过）
                season_dirs = [d for d in existing_dir.iterdir()
                              if d.is_dir() and d.name.startswith('Season ')]
                if season_dirs:
                    # 计算下一个季号
                    max_season = 0
                    for sd in season_dirs:
                        match = _re.search(r'Season\s+(\d+)', sd.name)
                        if match:
                            max_season = max(max_season, int(match.group(1)))
                    logger.info(f"检测到已存在的系列目录 {existing_dir.name}，当前最高季号 {max_season}，新视频将作为 Season {max_season + 1}")
                    return existing_dir.name, max_season + 1, True
            return default_series_name, 0, False

        # 有同系列视频信息，按 video_id 排序
        all_series_ids = sorted(set([sv["video_id"] for sv in detected_series_videos] + [video_id]))
        # 构建 video_id -> title 的映射
        id_title_map = {sv["video_id"]: sv["title"] for sv in detected_series_videos}
        id_title_map[video_id] = current_title

        # 检查 series 数据库表，看是否已经有合并记录
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT series_name, season_number FROM series WHERE video_id = ?",
                (video_id,)
            ) as cursor:
                existing_series = await cursor.fetchone()
                if existing_series:
                    return existing_series['series_name'], existing_series['season_number'], True

            # 检查同系列其他视频是否已下载
            for sv_info in detected_series_videos:
                sv_id = sv_info["video_id"]
                async with conn.execute(
                    "SELECT filename, title FROM downloads WHERE username = ? AND video_id = ? AND status = 'completed'",
                    (username, sv_id)
                ) as cursor2:
                    existing_dl = await cursor2.fetchone()
                    logger.info(f"系列检测: 查询同系列视频下载记录 video_id={sv_id}, found={existing_dl is not None}")
                    if existing_dl:
                        # 找到同系列已下载的视频！
                        existing_filename = existing_dl['filename']
                        # 从数据库记录的 filename 中提取实际目录名
                        existing_series_dir_name = existing_filename.split('/')[0] if '/' in existing_filename else None

                        # 确定实际磁盘上的目录路径
                        # 优先使用数据库记录中的目录名，如果磁盘上不存在再尝试查找
                        actual_series_dir = None
                        actual_series_dir_name = None

                        if existing_series_dir_name:
                            db_dir = settings.DOWNLOAD_PATH / existing_series_dir_name
                            if db_dir.exists():
                                actual_series_dir = db_dir
                                actual_series_dir_name = existing_series_dir_name

                        # 如果数据库记录的目录不存在（可能被刮削服务重命名了），在磁盘上查找
                        if not actual_series_dir:
                            # 从数据库记录中提取基础名（去掉可能的年份后缀）
                            base_dir_name = _re.sub(r'\s*\(\d{4}\)$', '', existing_series_dir_name) if existing_series_dir_name else default_series_name
                            found_dir = _find_series_dir_on_disk(base_dir_name)
                            if found_dir:
                                actual_series_dir = found_dir
                                actual_series_dir_name = found_dir.name

                        # 最后回退：直接用默认系列名查找
                        if not actual_series_dir:
                            found_dir = _find_series_dir_on_disk(default_series_name)
                            if found_dir:
                                actual_series_dir = found_dir
                                actual_series_dir_name = found_dir.name

                        if actual_series_dir:
                            # 如果目录名与默认系列名不同，重命名为系列基础名
                            # 但要注意：如果目录名有年份后缀是刮削服务加的，保留它
                            target_series_name = actual_series_dir_name
                            if actual_series_dir_name != default_series_name:
                                # 检查是否只是年份后缀不同，如果是则保持实际名称
                                base_actual = _re.sub(r'\s*\(\d{4}\)$', '', actual_series_dir_name)
                                if base_actual == default_series_name:
                                    # 只是年份后缀差异，保留实际目录名（刮削服务可能已添加）
                                    logger.info(f"系列检测: 目录名有年份后缀 {actual_series_dir_name}，保留实际名称")
                                    target_series_name = actual_series_dir_name

                            # 检查该目录是否已经是多季结构
                            season_dirs = [d for d in actual_series_dir.iterdir()
                                          if d.is_dir() and d.name.startswith('Season ')]

                            # === 一季多集策略（v3.3.3 回归标准电视剧结构）===
                            # 所有同系列视频统一放入 Season 1，对齐绿联NAS标准识别格式
                            # 集号由下载时按 Season 1 中已有视频数量+1 自动分配
                            season_number = 1

                            logger.info(f"检测到同系列已下载: {target_series_name}，"
                                      f"当前视频 {video_id} 副标题={current_subtitle}，"
                                      f"分配到 Season {season_number}（一季多集）")

                            return target_series_name, season_number, True

        # 没有找到已下载的同系列视频，使用系列基础名
        # 再次检查是否已有同系列目录（支持年份后缀）
        existing_dir = _find_series_dir_on_disk(default_series_name)
        if existing_dir:
            season_dirs = [d for d in existing_dir.iterdir()
                          if d.is_dir() and d.name.startswith('Season ')]
            if season_dirs:
                # 已有 Season 目录，新视频统一放入 Season 1（一季多集策略）
                return existing_dir.name, 1, True

        # 第一个视频下载（没有同系列已下载视频）
        # 一季多集策略：所有视频都放入 Season 1
        logger.info(f"系列检测: 首次下载 video_id={video_id}，"
                   f"副标题={current_subtitle}，分配到 Season 1（一季多集）")
        return default_series_name, 1, True

    # 中文数字到阿拉伯数字的映射（支持 1-99）
    _CN_DIGIT_MAP = {
        '零': 0, '〇': 0,
        '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9,
    }

    @classmethod
    def _cn_to_arabic(cls, cn: str) -> int:
        """
        中文数字转阿拉伯数字（支持 1-99）

        示例:
          '一' → 1, '二' → 2
          '十' → 10, '十一' → 11, '十九' → 19
          '二十' → 20, '二十一' → 21, '九十九' → 99
        """
        if not cn:
            return 0
        # 纯阿拉伯数字
        if cn.isdigit():
            return int(cn)
        # 单字
        if len(cn) == 1:
            if cn == '十':
                return 10
            return cls._CN_DIGIT_MAP.get(cn, 0)
        # 处理 "十X"（10-19）
        if cn.startswith('十'):
            rest = cn[1:]
            return 10 + cls._CN_DIGIT_MAP.get(rest, 0)
        # 处理 "X十"（20, 30, ...）
        if cn.endswith('十'):
            return cls._CN_DIGIT_MAP.get(cn[0], 0) * 10
        # 处理 "X十Y"（21-99）
        if '十' in cn:
            parts = cn.split('十')
            if len(parts) == 2:
                tens = cls._CN_DIGIT_MAP.get(parts[0], 0)
                ones = cls._CN_DIGIT_MAP.get(parts[1], 0)
                return tens * 10 + ones
        return 0

    def _extract_real_episode_number(self, title: str, subtitle: str = "") -> int:
        """
        从视频标题/副标题中提取真实集号（阿拉伯数字），失败返回 0

        优先级（高→低）：
        1. "第N話/话/期/章/部" - 含中文数字 "第十一話"→11、"第2話"→2
        2. "Episode N"、"Ep. N"、"EP N" - 英文标记
        3. "＃N"、"#N" - 数字标记
        4. "Season N" - 季号标记（也作为集号参考）
        5. 末尾罗马数字 "第Ⅱ"、"Ⅱ" - 1-5
        6. 末尾文字标签（前編=1, 後編=2, 上巻=1, 下巻=2, 中巻=2, OVA=99）
        7. 末尾阿拉伯数字 - "番剧名 10"→10

        注意：不会从标题中匹配年份（4 位数字 + 年/Year），避免误识别。
        """
        import re as _re

        if not title and not subtitle:
            return 0

        # 合并 title 和 subtitle，subtitle 优先（中文副标题更规范）
        candidates = []
        if subtitle:
            candidates.append(subtitle)
        if title:
            candidates.append(title)

        # 文字标签到集号的映射（前編=1, 後編=2 等）
        _LABEL_TO_EPISODE = {
            '上卷': 1, '上巻': 1, '前篇': 1, '前編': 1, '上篇': 1,
            '中卷': 2, '中巻': 2, '中篇': 2, '中編': 2,
            '下卷': 3, '下巻': 3, '後篇': 3, '後編': 3, '下篇': 3,
            '后篇': 3, '后編': 3, '下编': 3,
            'OVA': 99, '特典': 99, '番外': 99, '特別': 99, '特别': 99,
        }

        for text in candidates:
            if not text:
                continue
            text = text.strip()

            # 1. 匹配 "第N話/话/期/章/部/卷/篇/編" - 支持中文数字和阿拉伯数字
            # 例: "第十一話"→11, "第2話"→2, "第二期"→2
            m = _re.search(r'第\s*([零〇一二三四五六七八九十两\d]+)\s*[話话期章部卷篇編]', text)
            if m:
                num_str = m.group(1)
                if num_str.isdigit():
                    n = int(num_str)
                else:
                    n = self._cn_to_arabic(num_str)
                if n > 0:
                    return n

            # 2. 匹配 "Episode N"、"Ep. N"、"EP N"（不区分大小写）
            m = _re.search(r'(?:episode|ep\.?)\s*(\d+)', text, _re.IGNORECASE)
            if m:
                return int(m.group(1))

            # 3. 匹配 "＃N" 或 "#N"
            m = _re.search(r'[＃#]\s*(\d+)', text)
            if m:
                return int(m.group(1))

            # 4. 匹配 "Season N"（作为集号参考，避免误识别，只在没找到其他数字时使用）
            m = _re.search(r'[Ss]eason\s*(\d+)', text)
            if m:
                return int(m.group(1))

            # 5. 匹配罗马数字（"第Ⅱ"、"Ⅱ"等，必须以"第"开头或独立出现，避免误匹配"IIII"等）
            roman_map = {'Ⅰ': 1, 'Ⅱ': 2, 'Ⅲ': 3, 'Ⅳ': 4, 'Ⅴ': 5,
                         'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
            m = _re.search(r'第\s*([ⅠⅡⅢⅣⅤ]+)\s*[話话期章部]?', text)
            if m:
                roman = m.group(1)
                if roman in roman_map:
                    return roman_map[roman]
            # 独立罗马数字（标题末尾）
            m = _re.search(r'\s([ⅠⅡⅢⅣⅤ])\s*$', text)
            if m and m.group(1) in roman_map:
                return roman_map[m.group(1)]

            # 6. 文字标签（前編/後編/上巻/下巻等）
            for label in sorted(_LABEL_TO_EPISODE.keys(), key=len, reverse=True):
                if label in text:
                    return _LABEL_TO_EPISODE[label]

            # 7. 末尾阿拉伯数字 - 但要避免匹配年份（如 "2026" 不是集号）
            # 匹配 "番剧名 N" 或 "番剧名 N [中文字幕]" 格式
            # 先去掉 [中文字幕] 这类括号注释
            text_no_bracket = _re.sub(r'\s*\[[^\]]*\]\s*$', '', text).strip()
            m = _re.search(r'(\d+)\s*$', text_no_bracket)
            if m:
                n = int(m.group(1))
                # 排除明显是年份的数字（1900-2099）
                if not (1900 <= n <= 2099):
                    return n

        return 0

    def _sanitize_filename(self, filename):
        """处理文件名，移除非法字符"""
        # 替换非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
            
        return filename

    @staticmethod
    def _convert_to_poster_url(cover_url: str) -> str:
        """
        将缩略图URL转换为首页海报URL（仅用于URL格式推断，实际下载可能因secure token不匹配而403）
        优先使用 get_video_detail 返回的 cover 格式URL
        """
        if not cover_url:
            return cover_url
        # /image/thumbnail/407019l.jpg → /image/cover/407019.jpg
        # /image/thumbnail/407019h.jpg → /image/cover/407019.jpg
        import re
        converted = re.sub(
            r'/image/thumbnail/(\w+)[lh]\.jpg',
            r'/image/cover/\1.jpg',
            cover_url
        )
        return converted

    async def _get_cover_from_search(self, video_id: str, title: str) -> str:
        """
        通过视频详情页获取首页展示的海报封面URL（cover格式，竖版海报）
        不再使用搜索接口（搜索结果返回的是 thumbnail 格式，secure token 与 cover 格式不通用）
        :param video_id: 视频ID
        :param title: 视频标题（未使用，保留接口兼容）
        :return: cover 格式封面URL，失败时返回空字符串
        """
        try:
            video_detail = await self.video_service.get_video_detail(video_id)
            if video_detail and video_detail.cover_url and '/image/cover/' in video_detail.cover_url:
                logger.info(f"从视频详情页获取到 cover 海报: {video_detail.cover_url}")
                return video_detail.cover_url
            logger.warning(f"视频详情页未返回 cover 格式URL: {video_detail.cover_url if video_detail else 'N/A'}")
            return ""
        except Exception as e:
            logger.warning(f"通过视频详情页获取封面失败: {e}")
            return ""

    async def download_cover(self, video_id: str, cover_url: str, series_dir=None, filename: str = None) -> bool:
        """
        下载封面图片到番剧目录
        :param video_id: 视频ID
        :param cover_url: 封面URL
        :param series_dir: 番剧系列目录路径
        :param filename: 封面文件名（不含扩展名），默认使用 video_id
        :return: 是否下载成功
        """
        if not cover_url:
            return False

        try:
            # 封面保存到番剧目录中，以 video_id.jpg 命名
            cover_name = filename or video_id
            cover_filename = f"{cover_name}.jpg"

            # 优先保存到番剧目录
            if series_dir:
                cover_path = series_dir / cover_filename
            else:
                # 如果没有指定番剧目录，保存到全局封面目录
                os.makedirs(settings.COVER_PATH, exist_ok=True)
                cover_path = settings.COVER_PATH / cover_filename

            # 如果封面已存在，跳过下载
            if cover_path.exists():
                logger.info(f"封面已存在: {cover_path}")
                return True

            # 确保目录存在
            os.makedirs(os.path.dirname(cover_path), exist_ok=True)

            # 下载封面
            logger.info(f"开始下载封面: {cover_url}")
            client = await self.get_http_client(cover_url)

            async with client.stream("GET", cover_url, timeout=30.0) as response:
                if response.status_code != 200:
                    # 如果是cover格式URL但403，尝试用cf_bypasser下载
                    if response.status_code == 403 and '/image/cover/' in cover_url:
                        logger.info(f"cover URL 403，尝试用 cf_bypasser 下载")
                        try:
                            from app.utils.cloudflare_bypass import cf_bypasser
                            cf_client = await cf_bypasser.direct_client
                            cf_response = await cf_client.get(cover_url)
                            if cf_response and cf_response.status_code == 200:
                                content = cf_response.content
                                async with aiofiles.open(cover_path, "wb") as f:
                                    await f.write(content)
                                logger.success(f"通过 cf_bypasser 封面下载成功: {cover_path}")
                                return True
                            else:
                                logger.error(f"cf_bypasser 下载封面也失败: HTTP {cf_response.status_code if cf_response else 'N/A'}")
                                return False
                        except Exception as cf_e:
                            logger.error(f"cf_bypasser 下载封面异常: {cf_e}")
                            return False
                    logger.error(f"下载封面失败，状态码: {response.status_code}")
                    return False

                async with aiofiles.open(cover_path, "wb") as f:
                    async for chunk in response.aiter_bytes(8192):
                        await f.write(chunk)

            logger.success(f"封面下载成功: {cover_path}")
            return True

        except Exception as e:
            logger.error(f"下载封面失败: {str(e)}")
            return False

    async def get_http_client(self, url: str):
        """获取或创建HTTP客户端，实现连接池复用"""
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 检查是否已有相应域名的连接池
        if domain in self.http_clients:
            return self.http_clients[domain]
            
        # 设置httpx客户端选项
        client_options = {
            'timeout': httpx.Timeout(self.timeout, connect=self.timeout),
            'follow_redirects': True,
            'verify': False,  # 禁用SSL验证以处理特殊情况
            'limits': httpx.Limits(
                max_connections=self.connection_pool_size,
                max_keepalive_connections=self.connection_pool_size,
                keepalive_expiry=60  # 连接保持时间(秒)
            )
        }
        
        # 设置代理
        if settings.USE_DOWNLOAD_PROXY and settings.DOWNLOAD_PROXY_URL:
            client_options['proxies'] = settings.DOWNLOAD_PROXY_URL
            
        # 创建新的客户端
        client = httpx.AsyncClient(**client_options)
        self.http_clients[domain] = client
        return client
        
    async def close_http_clients(self):
        """关闭所有HTTP客户端连接"""
        for domain, client in self.http_clients.items():
            try:
                await client.aclose()
            except Exception as e:
                logger.error(f"关闭HTTP客户端失败 ({domain}): {str(e)}")
        self.http_clients = {}

    async def scan_and_restore_downloads(self, username: str) -> Dict[str, Any]:
        """
        扫描下载目录，恢复丢失的下载记录，并清理文件已不存在的无效记录

        第一阶段：从文件系统中发现已下载但数据库中无记录的文件，自动补建记录
        第二阶段：检查所有已完成的下载记录，如果对应文件已不存在（原始路径和刮削后路径都找不到），
                 则删除数据库记录
        """
        import re

        restored = []
        skipped = []
        errors = []
        removed = []

        download_path = settings.DOWNLOAD_PATH
        if not download_path.exists():
            return {"restored": [], "skipped": [], "errors": ["下载目录不存在"], "removed": []}

        # ========== 第一阶段：扫描恢复 ==========
        # 获取当前用户的所有下载记录video_id集合
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT video_id FROM downloads WHERE username = ?", (username,)
            ) as cursor:
                rows = await cursor.fetchall()
                existing_ids = {row['video_id'] for row in rows}

        # 扫描下载目录
        for series_dir in download_path.iterdir():
            if not series_dir.is_dir():
                continue

            series_name = series_dir.name

            # 遍历番剧目录中的视频文件
            for video_file in series_dir.iterdir():
                if not video_file.is_file():
                    continue
                if not video_file.suffix.lower() in ('.mp4', '.mkv', '.avi', '.wmv'):
                    continue

                # 从文件名解析 video_id（格式：{video_id}_{subtitle}.mp4）
                filename_stem = video_file.stem
                video_id = None

                # 尝试匹配 video_id_ 前缀
                match = re.match(r'^([a-zA-Z0-9]+?)_(.+)$', filename_stem)
                if match:
                    candidate_id = match.group(1)
                    # video_id 通常是纯数字或包含字母的短ID
                    if len(candidate_id) <= 20:
                        video_id = candidate_id

                if not video_id:
                    # 如果无法解析video_id，跳过
                    skipped.append({
                        "filename": video_file.name,
                        "series": series_name,
                        "reason": "无法解析video_id"
                    })
                    continue

                # 检查是否已有记录
                if video_id in existing_ids:
                    skipped.append({
                        "video_id": video_id,
                        "filename": video_file.name,
                        "reason": "记录已存在"
                    })
                    continue

                # 获取文件大小
                file_size = video_file.stat().st_size

                # 构建相对路径（与start_download格式一致）
                relative_path = f"{series_name}/{video_file.name}"

                # 检查是否有本地封面
                cover_url = ""
                cover_path = series_dir / f"{video_id}.jpg"
                if cover_path.exists():
                    cover_url = f"/api/downloads/cover/{video_id}"

                # 补建下载记录
                try:
                    async with aiosqlite.connect(self.db_path) as conn:
                        await conn.execute(
                            """INSERT OR REPLACE INTO downloads
                            (username, video_id, title, filename, cover_url, url, status, total_size, downloaded, retry_count, created_at, completed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                username,
                                video_id,
                                series_name,  # 标题先用系列名
                                relative_path,
                                cover_url,
                                "",  # URL不再有效，留空
                                DownloadStatus.COMPLETED,
                                file_size,
                                file_size,
                                0,
                                datetime.now().isoformat(),
                                datetime.now().isoformat()
                            )
                        )
                        await conn.commit()

                    existing_ids.add(video_id)
                    restored.append({
                        "video_id": video_id,
                        "filename": video_file.name,
                        "series": series_name,
                        "size": file_size
                    })
                    logger.info(f"恢复下载记录: {video_id} - {series_name}/{video_file.name}")

                except Exception as e:
                    errors.append({
                        "video_id": video_id,
                        "filename": video_file.name,
                        "error": str(e)
                    })
                    logger.error(f"恢复下载记录失败: {video_id} - {str(e)}")

        # ========== 第二阶段：清理无效记录 ==========
        # 检查所有已完成的下载记录，如果文件已不存在则删除记录
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT video_id, filename, status FROM downloads WHERE username = ? AND status = ?",
                (username, DownloadStatus.COMPLETED)
            ) as cursor:
                completed_rows = await cursor.fetchall()

        for row in completed_rows:
            vid = row['video_id']
            filename = row['filename']

            if not filename:
                continue

            # 1. 检查原始路径文件是否存在
            original_path = settings.DOWNLOAD_PATH / filename
            if await aiofiles.os.path.exists(original_path):
                continue

            # 2. 检查刮削后文件是否仍存在（通过 NFO 查找）
            series_name = filename.split('/')[0] if '/' in filename else None
            file_found_via_nfo = False
            if series_name:
                series_dir = settings.DOWNLOAD_PATH / series_name
                nfo_files = await self._find_nfo_by_video_id(series_dir, vid)
                if nfo_files:
                    file_found_via_nfo = True

            # 3. 原始路径和刮削后路径都找不到文件，删除记录
            if not file_found_via_nfo:
                try:
                    async with aiosqlite.connect(self.db_path) as conn:
                        await conn.execute(
                            "DELETE FROM downloads WHERE username = ? AND video_id = ?",
                            (username, vid)
                        )
                        await conn.commit()

                    # 清理内存中的记录
                    if vid in self.active_downloads:
                        del self.active_downloads[vid]

                    removed.append({
                        "video_id": vid,
                        "filename": filename,
                        "reason": "文件不存在（原始路径和刮削后路径均未找到）"
                    })
                    logger.info(f"清理无效下载记录: {vid} - {filename}")
                except Exception as e:
                    errors.append({
                        "video_id": vid,
                        "filename": filename,
                        "error": f"清理记录失败: {str(e)}"
                    })
                    logger.error(f"清理无效下载记录失败: {vid} - {str(e)}")

        return {
            "restored": restored,
            "skipped": skipped,
            "errors": errors,
            "removed": removed,
            "total_restored": len(restored),
            "total_removed": len(removed)
        }

    async def search_downloads(self, username: str, query: str = "", status: str = "") -> List[Dict[str, Any]]:
        """
        搜索下载记录
        :param username: 用户名
        :param query: 搜索关键词（匹配标题或文件名）
        :param status: 按状态过滤
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            conditions = ["username = ?"]
            params = [username]
            
            if query:
                conditions.append("(title LIKE ? OR filename LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = " AND ".join(conditions)
            
            async with db.execute(
                f"SELECT * FROM downloads WHERE {where_clause} ORDER BY created_at DESC",
                params
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def clear_completed_downloads(self, username: str) -> int:
        """清除所有已完成的下载记录（不删除文件）"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "DELETE FROM downloads WHERE username = ? AND status = 'completed'",
                (username,)
            )
            await conn.commit()
            return cursor.rowcount

    async def clear_failed_downloads(self, username: str) -> int:
        """清除所有失败的下载记录"""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "DELETE FROM downloads WHERE username = ? AND status IN ('error', 'cancelled')",
                (username,)
            )
            await conn.commit()
            return cursor.rowcount

    async def get_download_groups(self, username: str) -> List[Dict[str, Any]]:
        """
        获取按番剧系列分组的下载列表
        从数据库中按title字段分组，返回每个番剧的概要信息
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 获取用户所有下载记录
            async with db.execute(
                "SELECT * FROM downloads WHERE username = ? ORDER BY created_at DESC",
                (username,)
            ) as cursor:
                rows = await cursor.fetchall()
                all_downloads = [dict(row) for row in rows]
        
        # 按番剧目录名分组（从filename提取）
        groups = {}
        for dl in all_downloads:
            filename = dl.get('filename', '')
            series_name = filename.split('/')[0] if '/' in filename else (dl.get('title') or '未知番剧')
            
            if series_name not in groups:
                groups[series_name] = {
                    'series_name': series_name,
                    'cover_url': '',
                    'downloads': [],
                    'total_size': 0,
                    'completed_count': 0,
                    'downloading_count': 0,
                    'failed_count': 0,
                }
            
            # 用第一个有封面的记录作为组封面
            if not groups[series_name]['cover_url'] and dl.get('cover_url'):
                groups[series_name]['cover_url'] = dl['cover_url']
            
            groups[series_name]['downloads'].append(dl)
            file_size = dl.get('total_size') or 0
            groups[series_name]['total_size'] += file_size
            
            status = dl.get('status', '')
            if status == 'completed':
                groups[series_name]['completed_count'] += 1
            elif status in ('downloading', 'paused', 'pending'):
                groups[series_name]['downloading_count'] += 1
            elif status in ('error', 'cancelled'):
                groups[series_name]['failed_count'] += 1
        
        return list(groups.values())


# 创建下载管理器实例
download_manager = DownloadManager() 