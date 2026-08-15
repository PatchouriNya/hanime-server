from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.user import FavoritesResponse, WatchLaterResponse, PlaylistsResponse, WatchHistoryResponse, VideoActionResponse
from app.services.user_service import user_service
from app.config import logger
from app.utils.auth import get_current_user

router = APIRouter()


def _get_db_params(user: dict) -> tuple:
    """从用户字典中提取数据库参数"""
    return user.get("db_type", "local"), user.get("db_user_id")


@router.get("/favorites", response_model=FavoritesResponse)
async def get_favorites(user: dict = Depends(get_current_user)):
    """获取收藏列表"""
    db_type, db_user_id = _get_db_params(user)
    favorites = await user_service.get_favorites(user["username"], db_type=db_type, db_user_id=db_user_id)
    return FavoritesResponse(favorites=favorites)


@router.post("/favorites", response_model=VideoActionResponse)
async def add_favorite(video_id: str = Query(...), title: str = Query(...), cover_url: str = Query(...), user: dict = Depends(get_current_user)):
    """添加收藏"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.add_favorite(user["username"], video_id, title, cover_url, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="添加收藏成功")
    raise HTTPException(status_code=500, detail="添加收藏失败")


@router.delete("/favorites/{video_id}", response_model=VideoActionResponse)
async def remove_favorite(video_id: str, user: dict = Depends(get_current_user)):
    """移除收藏"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.remove_favorite(user["username"], video_id, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="移除收藏成功")
    raise HTTPException(status_code=500, detail="移除收藏失败")


@router.get("/favorites/{video_id}", response_model=dict)
async def is_favorite(video_id: str, user: dict = Depends(get_current_user)):
    """检查是否已收藏"""
    db_type, db_user_id = _get_db_params(user)
    is_fav = await user_service.is_favorite(user["username"], video_id, db_type=db_type, db_user_id=db_user_id)
    return {"is_favorite": is_fav}


@router.get("/watch_later", response_model=WatchLaterResponse)
async def get_watch_later(user: dict = Depends(get_current_user)):
    """获取稍后观看列表"""
    db_type, db_user_id = _get_db_params(user)
    watch_later = await user_service.get_watch_later(user["username"], db_type=db_type, db_user_id=db_user_id)
    return WatchLaterResponse(watch_later=watch_later)


@router.post("/watch_later", response_model=VideoActionResponse)
async def add_watch_later(video_id: str = Query(...), title: str = Query(...), cover_url: str = Query(...), user: dict = Depends(get_current_user)):
    """添加稍后观看"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.add_watch_later(user["username"], video_id, title, cover_url, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="添加稍后观看成功")
    raise HTTPException(status_code=500, detail="添加稍后观看失败")


@router.delete("/watch_later/{video_id}", response_model=VideoActionResponse)
async def remove_watch_later(video_id: str, user: dict = Depends(get_current_user)):
    """移除稍后观看"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.remove_watch_later(user["username"], video_id, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="移除稍后观看成功")
    raise HTTPException(status_code=500, detail="移除稍后观看失败")


@router.get("/watch_later/{video_id}", response_model=dict)
async def is_watch_later(video_id: str, user: dict = Depends(get_current_user)):
    """检查是否在稍后观看列表"""
    db_type, db_user_id = _get_db_params(user)
    is_wl = await user_service.is_watch_later(user["username"], video_id, db_type=db_type, db_user_id=db_user_id)
    return {"is_watch_later": is_wl}


@router.get("/playlists", response_model=PlaylistsResponse)
async def get_playlists(user: dict = Depends(get_current_user)):
    """获取所有播放清单"""
    db_type, db_user_id = _get_db_params(user)
    playlists = await user_service.get_playlists(user["username"], db_type=db_type, db_user_id=db_user_id)
    return PlaylistsResponse(playlists=playlists)


@router.post("/playlists", response_model=dict)
async def create_playlist(name: str = Query(...), user: dict = Depends(get_current_user)):
    """创建播放清单"""
    db_type, db_user_id = _get_db_params(user)
    playlist = await user_service.create_playlist(user["username"], name, db_type=db_type, db_user_id=db_user_id)
    if playlist:
        return {"success": True, "message": "创建播放清单成功", "playlist": playlist.dict()}
    raise HTTPException(status_code=500, detail="创建播放清单失败")


@router.delete("/playlists/{playlist_id}", response_model=VideoActionResponse)
async def delete_playlist(playlist_id: str, user: dict = Depends(get_current_user)):
    """删除播放清单"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.delete_playlist(user["username"], playlist_id, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="删除播放清单成功")
    raise HTTPException(status_code=500, detail="删除播放清单失败")


@router.get("/playlists/{playlist_id}", response_model=dict)
async def get_playlist(playlist_id: str, user: dict = Depends(get_current_user)):
    """获取单个播放清单"""
    db_type, db_user_id = _get_db_params(user)
    playlist = await user_service.get_playlist(user["username"], playlist_id, db_type=db_type, db_user_id=db_user_id)
    if playlist:
        return {"success": True, "playlist": playlist.dict()}
    raise HTTPException(status_code=404, detail="播放清单不存在")


@router.post("/playlists/{playlist_id}/videos", response_model=VideoActionResponse)
async def add_video_to_playlist(
    playlist_id: str,
    video_id: str = Query(...),
    title: str = Query(...),
    cover_url: str = Query(...),
    user: dict = Depends(get_current_user)
):
    """添加视频到播放清单"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.add_video_to_playlist(user["username"], playlist_id, video_id, title, cover_url, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="添加视频成功")
    raise HTTPException(status_code=500, detail="添加视频失败")


@router.delete("/playlists/{playlist_id}/videos/{video_id}", response_model=VideoActionResponse)
async def remove_video_from_playlist(playlist_id: str, video_id: str, user: dict = Depends(get_current_user)):
    """从播放清单移除视频"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.remove_video_from_playlist(user["username"], playlist_id, video_id, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="移除视频成功")
    raise HTTPException(status_code=500, detail="移除视频失败")


@router.put("/playlists/{playlist_id}", response_model=VideoActionResponse)
async def update_playlist_name(playlist_id: str, name: str = Query(...), user: dict = Depends(get_current_user)):
    """更新播放清单名称"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.update_playlist_name(user["username"], playlist_id, name, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="更新名称成功")
    raise HTTPException(status_code=500, detail="更新名称失败")


@router.post("/playlists/move-video", response_model=VideoActionResponse)
async def move_video_between_playlists(
    from_playlist_id: str = Query(...),
    to_playlist_id: str = Query(...),
    video_id: str = Query(...),
    user: dict = Depends(get_current_user)
):
    """将视频从一个清单移动到另一个清单"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.move_video_between_playlists(
        user["username"], from_playlist_id, to_playlist_id, video_id, db_type=db_type, db_user_id=db_user_id
    )
    if success:
        return VideoActionResponse(success=True, message="移动成功")
    raise HTTPException(status_code=500, detail="移动失败")


@router.get("/history", response_model=WatchHistoryResponse)
async def get_watch_history(user: dict = Depends(get_current_user)):
    """获取观看历史"""
    db_type, db_user_id = _get_db_params(user)
    history = await user_service.get_watch_history(user["username"], db_type=db_type, db_user_id=db_user_id)
    return WatchHistoryResponse(history=history)


@router.post("/history", response_model=VideoActionResponse)
async def add_watch_history(
    video_id: str = Query(...),
    title: str = Query(...),
    cover_url: str = Query(...),
    progress: int = Query(0),
    duration: str = Query(""),
    user: dict = Depends(get_current_user)
):
    """添加观看历史"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.add_watch_history(user["username"], video_id, title, cover_url, progress, duration, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="添加观看历史成功")
    raise HTTPException(status_code=500, detail="添加观看历史失败")


@router.delete("/history", response_model=VideoActionResponse)
async def clear_watch_history(user: dict = Depends(get_current_user)):
    """清空观看历史"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.clear_watch_history(user["username"], db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="清空观看历史成功")
    raise HTTPException(status_code=500, detail="清空观看历史失败")


@router.delete("/history/{video_id}", response_model=VideoActionResponse)
async def remove_watch_history(video_id: str, user: dict = Depends(get_current_user)):
    """从观看历史移除单个视频"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.remove_watch_history(user["username"], video_id, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="移除观看历史成功")
    raise HTTPException(status_code=500, detail="移除观看历史失败")


@router.get("/settings", response_model=dict)
async def get_user_settings(user: dict = Depends(get_current_user)):
    """获取用户设置"""
    db_type, db_user_id = _get_db_params(user)
    settings = await user_service.get_user_settings(user["username"], db_type=db_type, db_user_id=db_user_id)
    return {"success": True, "settings": settings}


@router.post("/settings", response_model=dict)
async def save_user_settings(settings: dict, user: dict = Depends(get_current_user)):
    """保存用户设置"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.save_user_settings(user["username"], settings, db_type=db_type, db_user_id=db_user_id)
    if success:
        return {"success": True, "message": "保存设置成功"}
    raise HTTPException(status_code=500, detail="保存设置失败")


# ==================== 番剧追更订阅（v4.0.0） ====================

@router.get("/subscriptions", response_model=dict)
async def get_subscriptions(user: dict = Depends(get_current_user)):
    """获取订阅的番剧系列列表"""
    db_type, db_user_id = _get_db_params(user)
    subscriptions = await user_service.get_subscriptions(user["username"], db_type=db_type, db_user_id=db_user_id)
    return {"success": True, "subscriptions": subscriptions}


@router.post("/subscriptions", response_model=VideoActionResponse)
async def add_subscription(series_name: str = Query(...), user: dict = Depends(get_current_user)):
    """订阅番剧系列（追更）"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.add_subscription(user["username"], series_name, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="订阅成功，有新集时会提醒")
    raise HTTPException(status_code=500, detail="订阅失败")


@router.delete("/subscriptions/{series_name}", response_model=VideoActionResponse)
async def remove_subscription(series_name: str, user: dict = Depends(get_current_user)):
    """取消订阅番剧系列"""
    db_type, db_user_id = _get_db_params(user)
    success = await user_service.remove_subscription(user["username"], series_name, db_type=db_type, db_user_id=db_user_id)
    if success:
        return VideoActionResponse(success=True, message="已取消订阅")
    raise HTTPException(status_code=500, detail="取消订阅失败")


@router.get("/subscriptions/check", response_model=dict)
async def check_subscriptions(user: dict = Depends(get_current_user)):
    """
    检查订阅系列是否有新集（追更提醒）

    对每个订阅系列：
    - 从源站搜索该系列最新上架的视频（取前几条）
    - 对比本地已下载的最新集号
    - 返回是否有新集及最新集信息
    """
    from app.services.video_service import VideoService
    from app.services.download_service import download_manager

    db_type, db_user_id = _get_db_params(user)
    subscriptions = await user_service.get_subscriptions(user["username"], db_type=db_type, db_user_id=db_user_id)

    video_service = VideoService()
    results = []
    for series_name in subscriptions:
        try:
            # 源站搜索该系列最新上架的视频
            search = await video_service.search_videos(
                query=series_name, genre=None, tags=None, broad=None,
                sort="最新上市", year=None, month=None, page=1
            )
            latest_videos = search.detailed_videos or []
            latest_episode = None
            if latest_videos:
                latest_episode = {
                    "video_id": latest_videos[0].video_id,
                    "title": latest_videos[0].title,
                    "cover_url": latest_videos[0].cover_url or ""
                }

            # 本地已下载信息
            downloaded_count = await download_manager.count_downloaded_in_series(user["username"], series_name)
            local_max_episode = await download_manager.get_latest_downloaded_episode(user["username"], series_name)

            # 源站最新集号（从标题提取 SxxExx 或数字，失败则用视频数估算）
            source_episode = None
            if latest_videos:
                import re as _re
                m = _re.search(r'S\d+E(\d+)', latest_videos[0].title or "", _re.IGNORECASE)
                if m:
                    source_episode = int(m.group(1))

            has_new = False
            if source_episode is not None and local_max_episode is not None:
                has_new = source_episode > local_max_episode
            elif latest_episode and local_max_episode is None and downloaded_count == 0:
                # 订阅了但一集都没下载 → 视为有新内容（供一键下载）
                has_new = True

            results.append({
                "series_name": series_name,
                "latest_episode": latest_episode,
                "downloaded_count": downloaded_count,
                "local_max_episode": local_max_episode,
                "source_episode": source_episode,
                "has_new": has_new
            })
        except Exception as e:
            from app.config import logger
            logger.warning(f"检查订阅更新失败: {series_name}: {e}")
            results.append({
                "series_name": series_name,
                "latest_episode": None,
                "downloaded_count": 0,
                "local_max_episode": None,
                "source_episode": None,
                "has_new": False,
                "error": str(e)
            })

    return {"success": True, "results": results}
