from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.user import FavoritesResponse, WatchLaterResponse, PlaylistsResponse, WatchHistoryResponse, VideoActionResponse
from app.services.user_service import user_service
from app.config import logger
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/favorites", response_model=FavoritesResponse)
async def get_favorites(user: dict = Depends(get_current_user)):
    """获取收藏列表"""
    favorites = await user_service.get_favorites(user["username"])
    return FavoritesResponse(favorites=favorites)


@router.post("/favorites", response_model=VideoActionResponse)
async def add_favorite(video_id: str = Query(...), title: str = Query(...), cover_url: str = Query(...), user: dict = Depends(get_current_user)):
    """添加收藏"""
    success = await user_service.add_favorite(user["username"], video_id, title, cover_url)
    if success:
        return VideoActionResponse(success=True, message="添加收藏成功")
    raise HTTPException(status_code=500, detail="添加收藏失败")


@router.delete("/favorites/{video_id}", response_model=VideoActionResponse)
async def remove_favorite(video_id: str, user: dict = Depends(get_current_user)):
    """移除收藏"""
    success = await user_service.remove_favorite(user["username"], video_id)
    if success:
        return VideoActionResponse(success=True, message="移除收藏成功")
    raise HTTPException(status_code=500, detail="移除收藏失败")


@router.get("/favorites/{video_id}", response_model=dict)
async def is_favorite(video_id: str, user: dict = Depends(get_current_user)):
    """检查是否已收藏"""
    is_fav = await user_service.is_favorite(user["username"], video_id)
    return {"is_favorite": is_fav}


@router.get("/watch_later", response_model=WatchLaterResponse)
async def get_watch_later(user: dict = Depends(get_current_user)):
    """获取稍后观看列表"""
    watch_later = await user_service.get_watch_later(user["username"])
    return WatchLaterResponse(watch_later=watch_later)


@router.post("/watch_later", response_model=VideoActionResponse)
async def add_watch_later(video_id: str = Query(...), title: str = Query(...), cover_url: str = Query(...), user: dict = Depends(get_current_user)):
    """添加稍后观看"""
    success = await user_service.add_watch_later(user["username"], video_id, title, cover_url)
    if success:
        return VideoActionResponse(success=True, message="添加稍后观看成功")
    raise HTTPException(status_code=500, detail="添加稍后观看失败")


@router.delete("/watch_later/{video_id}", response_model=VideoActionResponse)
async def remove_watch_later(video_id: str, user: dict = Depends(get_current_user)):
    """移除稍后观看"""
    success = await user_service.remove_watch_later(user["username"], video_id)
    if success:
        return VideoActionResponse(success=True, message="移除稍后观看成功")
    raise HTTPException(status_code=500, detail="移除稍后观看失败")


@router.get("/watch_later/{video_id}", response_model=dict)
async def is_watch_later(video_id: str, user: dict = Depends(get_current_user)):
    """检查是否在稍后观看列表"""
    is_wl = await user_service.is_watch_later(user["username"], video_id)
    return {"is_watch_later": is_wl}


@router.get("/playlists", response_model=PlaylistsResponse)
async def get_playlists(user: dict = Depends(get_current_user)):
    """获取所有播放清单"""
    playlists = await user_service.get_playlists(user["username"])
    return PlaylistsResponse(playlists=playlists)


@router.post("/playlists", response_model=dict)
async def create_playlist(name: str = Query(...), user: dict = Depends(get_current_user)):
    """创建播放清单"""
    playlist = await user_service.create_playlist(user["username"], name)
    if playlist:
        return {"success": True, "message": "创建播放清单成功", "playlist": playlist.dict()}
    raise HTTPException(status_code=500, detail="创建播放清单失败")


@router.delete("/playlists/{playlist_id}", response_model=VideoActionResponse)
async def delete_playlist(playlist_id: str, user: dict = Depends(get_current_user)):
    """删除播放清单"""
    success = await user_service.delete_playlist(user["username"], playlist_id)
    if success:
        return VideoActionResponse(success=True, message="删除播放清单成功")
    raise HTTPException(status_code=500, detail="删除播放清单失败")


@router.get("/playlists/{playlist_id}", response_model=dict)
async def get_playlist(playlist_id: str, user: dict = Depends(get_current_user)):
    """获取单个播放清单"""
    playlist = await user_service.get_playlist(user["username"], playlist_id)
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
    success = await user_service.add_video_to_playlist(user["username"], playlist_id, video_id, title, cover_url)
    if success:
        return VideoActionResponse(success=True, message="添加视频成功")
    raise HTTPException(status_code=500, detail="添加视频失败")


@router.delete("/playlists/{playlist_id}/videos/{video_id}", response_model=VideoActionResponse)
async def remove_video_from_playlist(playlist_id: str, video_id: str, user: dict = Depends(get_current_user)):
    """从播放清单移除视频"""
    success = await user_service.remove_video_from_playlist(user["username"], playlist_id, video_id)
    if success:
        return VideoActionResponse(success=True, message="移除视频成功")
    raise HTTPException(status_code=500, detail="移除视频失败")


@router.put("/playlists/{playlist_id}", response_model=VideoActionResponse)
async def update_playlist_name(playlist_id: str, name: str = Query(...), user: dict = Depends(get_current_user)):
    """更新播放清单名称"""
    success = await user_service.update_playlist_name(user["username"], playlist_id, name)
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
    success = await user_service.move_video_between_playlists(
        user["username"], from_playlist_id, to_playlist_id, video_id
    )
    if success:
        return VideoActionResponse(success=True, message="移动成功")
    raise HTTPException(status_code=500, detail="移动失败")


@router.get("/history", response_model=WatchHistoryResponse)
async def get_watch_history(user: dict = Depends(get_current_user)):
    """获取观看历史"""
    history = await user_service.get_watch_history(user["username"])
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
    success = await user_service.add_watch_history(user["username"], video_id, title, cover_url, progress, duration)
    if success:
        return VideoActionResponse(success=True, message="添加观看历史成功")
    raise HTTPException(status_code=500, detail="添加观看历史失败")


@router.delete("/history", response_model=VideoActionResponse)
async def clear_watch_history(user: dict = Depends(get_current_user)):
    """清空观看历史"""
    success = await user_service.clear_watch_history(user["username"])
    if success:
        return VideoActionResponse(success=True, message="清空观看历史成功")
    raise HTTPException(status_code=500, detail="清空观看历史失败")


@router.delete("/history/{video_id}", response_model=VideoActionResponse)
async def remove_watch_history(video_id: str, user: dict = Depends(get_current_user)):
    """从观看历史移除单个视频"""
    success = await user_service.remove_watch_history(user["username"], video_id)
    if success:
        return VideoActionResponse(success=True, message="移除观看历史成功")
    raise HTTPException(status_code=500, detail="移除观看历史失败")


@router.get("/settings", response_model=dict)
async def get_user_settings(user: dict = Depends(get_current_user)):
    """获取用户设置"""
    settings = await user_service.get_user_settings(user["username"])
    return {"success": True, "settings": settings}


@router.post("/settings", response_model=dict)
async def save_user_settings(settings: dict, user: dict = Depends(get_current_user)):
    """保存用户设置"""
    success = await user_service.save_user_settings(user["username"], settings)
    if success:
        return {"success": True, "message": "保存设置成功"}
    raise HTTPException(status_code=500, detail="保存设置失败")
