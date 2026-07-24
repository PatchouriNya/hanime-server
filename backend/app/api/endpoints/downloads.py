from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from app.services.download_service import download_manager
from app.models.download import DownloadRequest, DownloadAction
from typing import List, Dict, Any, Optional
from app.config import settings, logger
from fastapi import APIRouter, Query, Depends
from fastapi.responses import FileResponse
from app.utils.auth import get_current_user, verify_token
import os

router = APIRouter()

@router.on_event("startup")
async def startup():
    """应用启动时初始化下载管理器"""
    await download_manager.init_db()
    logger.info("初始化数据库成功")
    await download_manager.load_downloads()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理，用于实时更新下载进度"""
    await websocket.accept()
    download_manager.websocket_connections.add(websocket)
    try:
        # 连接建立后发送现有下载状态
        for video_id, download in download_manager.active_downloads.items():
            await download_manager.broadcast_progress(video_id)
            
        # 保持连接，直到客户端断开
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        download_manager.websocket_connections.remove(websocket)


@router.get("/history")
async def get_download_history(
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="按状态过滤"),
    user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取下载历史记录，支持搜索和过滤"""
    if search or status:
        return await download_manager.search_downloads(user["username"], query=search or "", status=status or "")
    return await download_manager.get_download_history(user["username"])


@router.get("/groups")
async def get_download_groups(user: dict = Depends(get_current_user)):
    """获取按番剧系列分组的下载列表"""
    return await download_manager.get_download_groups(user["username"])


@router.post("/scan")
async def scan_and_restore(user: dict = Depends(get_current_user)):
    """扫描下载目录，恢复丢失的下载记录"""
    result = await download_manager.scan_and_restore_downloads(user["username"])
    return result


@router.post("/start")
async def start_download(download_request: DownloadRequest, user: dict = Depends(get_current_user)):
    """开始下载视频"""
    return await download_manager.start_download(
        download_request.video_id,
        user["username"],
        download_request.force
    )


@router.post("/action")
async def handle_download_action(action: DownloadAction, user: dict = Depends(get_current_user)):
    """处理下载操作(暂停/继续/取消/重试/删除)"""
    video_id = action.video_id
    action_type = action.action.lower()
    result = {"status": "error", "message": "无效的操作"}
    
    if action_type == "pause":
        success = await download_manager.pause_download(video_id)
        result = {"status": "success" if success else "error", "message": "暂停操作处理完成" if success else "操作失败"}
    elif action_type == "resume":
        success = await download_manager.resume_download(video_id)
        result = {"status": "success" if success else "error", "message": "继续操作处理完成" if success else "操作失败"}
    elif action_type == "cancel":
        success = await download_manager.cancel_download(video_id)
        result = {"status": "success" if success else "error", "message": "取消操作处理完成" if success else "操作失败"}
    elif action_type == "retry":
        success = await download_manager.retry_download(video_id)
        result = {"status": "success" if success else "error", "message": "重试操作处理完成" if success else "操作失败"}
    elif action_type == "delete":
        success = await download_manager.delete_download(video_id, user["username"])
        result = {"status": "success" if success else "error", "message": "删除操作处理完成" if success else "操作失败"}
    elif action_type == "clear_completed":
        count = await download_manager.clear_completed_downloads(user["username"])
        result = {"status": "success", "message": f"已清除 {count} 条已完成记录"}
    elif action_type == "clear_failed":
        count = await download_manager.clear_failed_downloads(user["username"])
        result = {"status": "success", "message": f"已清除 {count} 条失败记录"}
    
    return result


@router.get("/file/{video_id}")
async def get_downloaded_file(video_id: str, user: dict = Depends(get_current_user)):
    """获取已下载的文件"""
    # 检查视频是否存在且已下载完成
    download_info = await download_manager.check_existing_download(video_id, user["username"])
    if not download_info:
        return {"status": "error", "message": "下载记录不存在"}
    
    if download_info['status'] != 'completed':
        return {"status": "error", "message": "下载尚未完成"}
    
    file_path = settings.DOWNLOAD_PATH / download_info['filename']
    if not os.path.exists(file_path):
        return {"status": "error", "message": "文件不存在"}
    
    return FileResponse(
        path=file_path,
        filename=download_info['filename'],
        media_type='video/mp4'
    )


cover_router = APIRouter()


@cover_router.post("/cover")
async def download_cover(
    video_id: str = Query(...),
    cover_url: str = Query(...),
    user: dict = Depends(get_current_user)
):
    """
    下载封面图片到 covers 目录
    cover_url 来自搜索接口（已修复为 main-thumb 封面海报，非播放预览截图）
    """
    try:
        covers_dir = settings.DOWNLOAD_PATH / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)

        # 使用 cf_bypasser 的 direct_client 下载封面（绕过 Cloudflare）
        from app.utils.cloudflare_bypass import cf_bypasser
        client = await cf_bypasser.direct_client
        response = await client.get(cover_url)

        if not response or response.status_code != 200:
            return {"success": False, "message": f"封面下载失败: HTTP {response.status_code if response else 'N/A'}"}

        content = response.content
        content_type = response.headers.get("content-type", "")

        # 确定扩展名
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            ext = ".jpg"

        # 保存原始文件
        original_path = covers_dir / f"{video_id}{ext}"
        with open(original_path, "wb") as f:
            f.write(content)

        # 如果不是JPG，也转换一份JPG
        if ext != ".jpg":
            try:
                from PIL import Image
                img = Image.open(original_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                jpg_path = covers_dir / f"{video_id}.jpg"
                img.save(jpg_path, "JPEG", quality=95, subsampling=0)
                img.close()
            except ImportError:
                pass

        file_size = len(content)
        logger.info(f"封面已下载: {video_id}, 大小: {file_size}字节, URL: {cover_url}")
        return {"success": True, "message": f"封面已保存到 {covers_dir}", "file_size": file_size}

    except Exception as e:
        logger.error(f"下载封面失败: {e}")
        return {"success": False, "message": str(e)}


@cover_router.get("/cover/{video_id}")
async def get_cover(video_id: str, token: Optional[str] = Query(None)):
    """
    获取本地封面图片
    优先从番剧目录查找，其次从全局封面目录查找
    如果都不存在，则实时获取视频详情并下载封面
    支持通过 query 参数 ?token=xxx 进行认证（供 <img> 标签使用）
    """
    if token:
        try:
            verify_token(token)
        except HTTPException:
            raise
    else:
        raise HTTPException(
            status_code=401,
            detail="缺少认证 token，请通过 ?token=xxx 参数提供",
        )
    cover_filename = f"{video_id}.jpg"

    # 1. 先在番剧目录中查找（遍历下载目录的子目录）
    for series_dir in settings.DOWNLOAD_PATH.iterdir():
        if series_dir.is_dir():
            cover_path = series_dir / cover_filename
            if cover_path.exists():
                return FileResponse(path=cover_path, media_type='image/jpeg')

    # 2. 在全局封面目录查找
    cover_path = settings.COVER_PATH / cover_filename
    if cover_path.exists():
        return FileResponse(path=cover_path, media_type='image/jpeg')

    # 3. 本地不存在，尝试下载
    logger.info(f"本地封面不存在，尝试下载视频 {video_id} 的封面")

    from app.services.video_service import VideoService
    video_service = VideoService()

    try:
        video_detail = await video_service.get_video_detail(video_id)
        if video_detail and video_detail.cover_url:
            # 查找该视频的番剧目录
            series_name = download_manager._sanitize_filename(video_detail.title)
            series_dir = settings.DOWNLOAD_PATH / series_name

            # 下载封面
            await download_manager.download_cover(video_id, video_detail.cover_url, series_dir, filename=video_id)

            # 再次检查
            if series_dir.exists():
                cover_path = series_dir / cover_filename
                if cover_path.exists():
                    return FileResponse(path=cover_path, media_type='image/jpeg')

            # 回退到全局封面目录
            cover_path = settings.COVER_PATH / cover_filename
            if cover_path.exists():
                return FileResponse(path=cover_path, media_type='image/jpeg')

            raise HTTPException(status_code=404, detail="封面下载失败")
        else:
            raise HTTPException(status_code=404, detail="无法获取视频信息")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取封面失败: {str(e)}")
        raise HTTPException(status_code=404, detail=f"获取封面失败: {str(e)}") 