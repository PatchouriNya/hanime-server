from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from app.models.video import *
from app.models.video import CalendarData
from app.services.video_service import VideoService
import httpx
from app.config import settings, logger
from app.utils.ttl_lru_cache import lru_cache
from app.utils.chinese_converter import convert_dict

router = APIRouter()
video_service = VideoService()


@router.get("/home", response_model=HomeData)
@lru_cache(maxsize=1, ttl=1800)  # 缓存过期时间30分钟
async def get_home_page():
    """获取首页数据，包括头图和推荐视频"""
    data = await video_service.get_home_data()
    # 附带版本信息，前端无需额外请求 /settings/version
    data.version = settings.APP_VERSION
    data.app_name = settings.APP_NAME
    data.app_description = settings.APP_DESCRIPTION
    return data


@router.get("/calendar", response_model=CalendarData)
@lru_cache(maxsize=1, ttl=3600)  # 缓存1小时
async def get_calendar():
    """获取日历/新番列表数据"""
    return await video_service.get_calendar_data()


@router.get("/search_combination", response_model=SearchCombination)
@lru_cache(maxsize=1, ttl=86400)  # 只缓存1个结果，过期时间24小时
async def get_search_combination():
    return await video_service.get_search_combination()


def _search_key_builder(*args, **kwargs):
    """为搜索接口创建缓存键"""
    # 提取所有查询参数
    query = kwargs.get("query", "")
    genre = kwargs.get("genre", "")
    tags = "-".join(kwargs.get("tags", []) or [])
    broad = str(kwargs.get("broad", False))
    sort = kwargs.get("sort", "")
    year = str(kwargs.get("year", ""))
    month = str(kwargs.get("month", ""))
    page = str(kwargs.get("page", 1))

    # 组合成键
    key = f"search:{query}:{genre}:{tags}:{broad}:{sort}:{year}:{month}:{page}"
    return key


@router.get("/search")
@lru_cache(maxsize=100, ttl=86400, key_builder=_search_key_builder)  # 缓存100个搜索结果，过期时间24小时
async def search_videos(
        query: str = Query(None, description="搜索关键词"),
        genre: Optional[str] = Query(None, description="视频类型过滤"),
        tags: Optional[List[str]] = Query(None, description="标签过滤"),
        broad: Optional[bool] = Query(False, description="宽泛搜索"),
        sort: Optional[str] = Query(None, description="排序方式"),
        year: Optional[int] = Query(None, description="年份"),
        month: Optional[int] = Query(None, description="月份"),
        page: int = Query(1, description="页码", ge=1)
):
    """搜索视频"""
    params = {
        "query": query,
        "genre": genre,
        "tags": tags,
        "broad": broad,
        "sort": sort,
        "year": year,
        "month": month,
        "page": page
    }
    return await video_service.search_videos(**convert_dict(params, to_simple=False))


@router.get("/detail/{video_id}", response_model=VideoDetail)
@lru_cache(maxsize=100, ttl=3600)  # 缓存100个视频详情，过期时间1小时
async def get_video_detail(video_id: str):
    """获取视频详情"""
    return await video_service.get_video_detail(video_id)


@router.get("/loadComments/{video_id}", response_model=List[VideoComment])
@lru_cache(maxsize=100, ttl=3600)
async def load_comments(video_id: str):
    """加载视频评论"""
    return await video_service.get_video_comments(video_id)


@router.get("/loadReplies/{comment_id}", response_model=List[CommentReply])
@lru_cache(maxsize=100, ttl=3600)
async def load_replies(comment_id: str):
    """加载评论回复"""
    return await video_service.get_comment_replies(comment_id)


@router.get("/stream/proxy")
async def stream_video(url: str, request: Request = None):
    """视频流式传输

    为前端提供视频流，通过后端代理访问原始视频URL

    v4.0.0 修复：此前在 `async with httpx.AsyncClient(...)` 块内 return StreamingResponse，
    StreamingResponse 是惰性的——实际流发送发生在响应返回之后，而那时 client 已被关闭，
    迭代已断开的连接导致流中断，浏览器收到损坏数据报 Format error (MEDIA_ERR_SRC_NOT_SUPPORTED)。
    现在通过 background=BackgroundTask(client.aclose) 把 client 生命周期延长到流发送完成后，
    并携带浏览器 User-Agent（源站 CDN 可能拒绝 python-httpx 默认 UA）。
    """

    if not url:
        raise HTTPException(status_code=400, detail="未提供视频URL")

    # 设置代理
    proxy = None
    if settings.USE_PROXY and settings.PROXY_URL:
        proxy = settings.PROXY_URL

    # 获取请求头中的Range信息
    range_header = request.headers.get("range")

    try:
        # v4.0.0: 使用 proxy= 参数（httpx 0.26+ 写法，proxies= 在 0.28 已移除）
        client_kwargs = {}
        if proxy:
            client_kwargs["proxy"] = proxy
        client = httpx.AsyncClient(**client_kwargs)

        # 如果有Range头，则将其转发到目标服务器
        headers = {
            # 携带浏览器 UA，避免源站 CDN 拒绝默认 python-httpx UA
            "user-agent": settings.USER_AGENT,
        }
        if range_header:
            headers["range"] = range_header

        # 发送请求到目标URL，包含可能的Range头
        response = await client.get(url, headers=headers, follow_redirects=True)

        # 准备响应头
        media_type = response.headers.get("content-type", "video/mp4")
        resp_headers = {
            "content-type": media_type,
            "accept-ranges": "bytes"
        }

        # 如果是范围请求，复制原始响应的Content-Range头
        status_code = 200
        if "content-range" in response.headers:
            resp_headers["content-range"] = response.headers["content-range"]
            status_code = 206  # Partial Content

        if "content-length" in response.headers:
            resp_headers["content-length"] = response.headers["content-length"]

        # 返回流式响应
        # v4.0.0: background 在流发送完成后才关闭 client，保证 aiter_bytes 期间连接存活
        return StreamingResponse(
            response.aiter_bytes(),
            headers=resp_headers,
            status_code=status_code,
            media_type=media_type,
            background=BackgroundTask(client.aclose)
        )
    except Exception as e:
        # 异常路径也要关闭 client，避免连接泄漏
        try:
            if 'client' in locals():
                await client.aclose()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"视频流获取失败: {str(e)}")
