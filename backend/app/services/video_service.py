from bs4 import BeautifulSoup
from bs4.element import Tag

from app.models.video import *
from app.models.video import CalendarDay, CalendarData
from app.config import settings, logger
from app.utils.cloudflare_bypass import cf_bypasser
from app.utils.chinese_converter import to_simplified, convert_dict, convert_list

import re
import json
import asyncio
from datetime import datetime


class VideoService:
    def __init__(self):
        """初始化视频服务"""
        self.cf_bypasser = cf_bypasser

    async def get_home_data(self) -> HomeData:
        """获取首页数据，包括头图和推荐视频"""
        try:
            page_content = await self.cf_bypasser.get_request(settings.HANIME_BASE_URL)
            if not page_content:
                raise Exception("Failed to fetch page content")

            soup = BeautifulSoup(page_content, 'lxml')

            banner_data = self._extract_banners_data(soup)

            recommended_elem = soup.find('div', id='home-rows-wrapper')
            if not recommended_elem:
                return HomeData(
                    banners=banner_data,
                    error="无法获取推荐视频数据"
                )

            other_video_sections = [
                {"name": "latest_videos", "display_name": "最新里番", "matcher": "裏番"},
                {"name": "new_arrivals_videos", "display_name": "最新上市", "matcher": "最新上市"},
                {"name": "new_uploads_videos", "display_name": "最新上传", "matcher": "最新上傳"},
                {"name": "popular_videos", "display_name": "他们在看", "matcher": "他們在看"},
                {"name": "ai_generated_videos", "display_name": "AI生成", "matcher": "AI生成"},
                {"name": "bubble_tea_videos", "display_name": "泡面番", "matcher": "泡麵番"},
            ]

            home_data = HomeData(banners=banner_data)

            for section in other_video_sections:
                section_name = section["name"]
                display_name = section["display_name"]
                matcher = section["matcher"]

                section_data = self._extract_section_videos(recommended_elem, matcher, display_name)
                setattr(home_data, section_name, section_data)

            try:
                daily_result, monthly_result = await asyncio.gather(
                    self.search_videos(query=None, genre=None, tags=None, broad=None, sort="本日排行", year=None, month=None, page=1),
                    self.search_videos(query=None, genre=None, tags=None, broad=None, sort="本月排行", year=None, month=None, page=1),
                )

                if daily_result.detailed_videos:
                    home_data.daily_rank_videos = [{
                        "title": "本日排行",
                        "search_suffix": "sort=本日排行",
                        "videos": daily_result.detailed_videos[:10]
                    }]

                if monthly_result.detailed_videos:
                    home_data.monthly_rank_videos = [{
                        "title": "本月排行",
                        "search_suffix": "sort=本月排行",
                        "videos": monthly_result.detailed_videos[:10]
                    }]
            except Exception as e:
                logger.warning(f"获取排行数据失败: {str(e)}")

            return home_data
        except Exception as e:
            logger.exception(f"首页数据获取错误: {str(e)}")
            raise

    def _extract_banners_data(self, soup: BeautifulSoup) -> List[BannerVideo]:
        """提取首页多个Banner数据"""
        banners = []
        # 方式1: 查找所有 banner wrapper
        banner_wrappers = soup.find_all('div', id='home-banner-wrapper')

        for banner_wrapper in banner_wrappers:
            try:
                banner_title_ele = banner_wrapper.find('h1')
                banner_desc_ele = banner_wrapper.find('h4')

                prev_div = banner_wrapper.find_previous_sibling('div')
                banner_img_ele = prev_div.find('img') if prev_div else None

                image_url = banner_img_ele.get('src', '') if banner_img_ele else ''
                video_id = self._extract_video_id_from_image(image_url)

                if image_url or video_id:
                    banners.append(BannerVideo(
                        video_id=video_id,
                        cover_url=image_url,
                        title=banner_title_ele.get_text(strip=True) if banner_title_ele else '',
                        description=banner_desc_ele.get_text(strip=True) if banner_desc_ele else ''
                    ))
            except Exception as e:
                logger.warning(f"提取Banner数据错误: {str(e)}")
                continue

        # 方式2: 如果方式1只找到一个或没找到，尝试从所有大图中查找
        if len(banners) < 3:
            # 从 latest_videos 中选取前几个有封面的视频作为轮播
            try:
                recommended_elem = soup.find('div', id='home-rows-wrapper')
                if recommended_elem:
                    all_links = recommended_elem.find_all('a', href=re.compile(r'/watch'))
                    seen_ids = {b.video_id for b in banners}
                    for link in all_links:
                        if len(banners) >= 5:
                            break
                        href = link.get('href', '')
                        vid = self._extract_video_id(href)
                        if not vid or vid in seen_ids:
                            continue
                        img = link.find('img')
                        if not img:
                            continue
                        cover = img.get('src', '')
                        title = img.get('alt', '') or ''
                        if not title:
                            title_elem = link.find('div', class_=lambda x: x and 'title' in x)
                            title = title_elem.get_text(strip=True) if title_elem else vid
                        banners.append(BannerVideo(
                            video_id=vid,
                            cover_url=cover,
                            title=title,
                            description=''
                        ))
                        seen_ids.add(vid)
            except Exception as e:
                logger.warning(f"提取额外Banner数据错误: {str(e)}")

        return banners

    def _extract_section_videos(self, recommended_elem: Tag, matcher: str, display_name: str) -> List[Dict[str, Any]]:
        """提取特定分区的视频列表"""
        section_videos = []

        section_ele = None
        for a in recommended_elem.find_all('a', href=True):
            href = a['href']
            if matcher in href:
                section_ele = a
                break

        if not section_ele:
            return []

        search_url = section_ele['href']
        search_suffix = search_url.split("?")[1] if search_url and "?" in search_url else ""

        # 根据 section 类型补充 sort 参数
        if search_suffix and "sort=" not in search_suffix:
            if "最新" in display_name or "里番" in display_name or "裏番" in display_name:
                search_suffix += "&sort=最新上市"
            elif "排行" in display_name:
                pass  # 排行已有 sort

        videos_div = section_ele.find_next_sibling('div')
        if not videos_div:
            return []

        video_elements = videos_div.find_all('div', title=True)

        video_info_list = []

        for video_ele in video_elements[:10]:
            video_info = self._extract_detailed_video_info(video_ele)
            if video_info:
                video_info_list.append(video_info)

        # search_suffix 保留繁体原文，不转简体
        section_videos.append({
            "title": display_name,
            "search_suffix": search_suffix,
            "videos": video_info_list
        })

        return section_videos

    def _extract_detailed_video_info(self, video_ele: Tag) -> Optional[VideoPreview]:
        """从单个 详细视频 元素中提取信息"""
        try:
            video_title = ""
            
            title_selectors = [
                video_ele.find('div', class_=lambda x: x and 'home-rows-videos-title' in x),
                video_ele.find('div', class_=lambda x: x and 'card-mobile-title' in x),
                video_ele.find('div', class_=lambda x: x and 'title' in x and not 'thumbnail' in x and not 'duration' in x),
                video_ele.find('span', class_=lambda x: x and 'title' in x),
                video_ele.find('h3'),
                video_ele.find('h4'),
                video_ele.find('a', class_=lambda x: x and 'video-link' in x),
                video_ele.find_parent('a'),
            ]
            
            for title_elem in title_selectors:
                if title_elem:
                    text = title_elem.get_text(strip=True)
                    if text and len(text) > 1:
                        video_title = text
                        break
            
            if not video_title:
                img_elem = video_ele.find('img')
                if img_elem:
                    video_title = img_elem.get('alt', '') or img_elem.get('title', '')

            overlay_ele = video_ele.find('a', class_=lambda x: x and 'video-link' in x)
            video_url = overlay_ele.get('href', '') if overlay_ele else ''

            video_id = self._extract_video_id_from_url(video_url)

            if not video_id:
                return None

            img_ele = video_ele.find('img', class_=lambda x: x and 'main-thumb' in x)
            img_url = img_ele.get('src', '') if img_ele else ''

            duration_ele = video_ele.find('div', class_=lambda x: x and 'duration' in x)
            duration_text = duration_ele.get_text(strip=True) if duration_ele else ''

            like_rate = ""
            views_text = ""

            stats_container = video_ele.find('div', class_=lambda x: x and 'stats-container' in x)
            if stats_container:
                stat_items = stats_container.find_all('div', class_=lambda x: x and 'stat-item' in x)
                
                if len(stat_items) >= 1:
                    like_text = stat_items[0].get_text(strip=True)
                    rate_match = re.search(r'(\d+%)', like_text)
                    if rate_match:
                        like_rate = rate_match.group(1)

                if len(stat_items) >= 2:
                    views_item = stat_items[1]
                    views_text = views_item.get_text(strip=True)

            studio = {}
            subtitle_div = video_ele.find('div', class_=lambda x: x and 'subtitle' in x)
            studio_ele = subtitle_div.find('a') if subtitle_div else None
            
            if studio_ele:
                full_text = studio_ele.get_text(strip=True)
                studio_name = full_text.split("•")[0].strip() if "•" in full_text else full_text
                studio_url = studio_ele.get('href', '')
                studio_query = studio_url.split("?")[1] if studio_url and "?" in studio_url else ""

                studio = VideoStudio(
                    name=studio_name,
                    query=studio_query
                )

            return VideoPreview(
                video_id=video_id,
                cover_url=img_url,
                title=video_title,
                duration=duration_text,
                view_count=self._parse_views(views_text),
                like_rate=like_rate,
                studio=studio
            )

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            logger.error(f"提取视频信息错误: {str(e)}")
            return None

    def _extract_detailed_video_info_old(self, video_ele: Tag) -> Optional[VideoPreview]:
        """老版本，但是系列视频用的是老版本的"""
        try:
            title_elem = video_ele.find(class_=lambda x: x and 'card-mobile-title' in x)
            video_title = title_elem.get_text(strip=True) if title_elem else ''

            overlay_ele = video_ele.find('a', class_='overlay')
            video_url = overlay_ele.get('href', '') if overlay_ele else ''

            video_id = self._extract_video_id_from_url(video_url)

            if not video_id:
                return None

            img_ele = video_ele.find('img', style=lambda x: x and 'object-fit: cover' in x)
            img_url = img_ele.get('src', '') if img_ele else ''

            duration_ele = video_ele.find('div', class_=lambda x: x and 'card-mobile-duration' in x and ':' in str(x))
            duration_text = duration_ele.get_text(strip=True) if duration_ele else ''

            like_rate = ""
            like_count = 0
            like_ele = video_ele.find('div', class_=lambda x: x and 'card-mobile-duration' in x)
            
            if like_ele and 'thumb_up' in str(like_ele):
                like_text = like_ele.get_text(strip=True)
                rate_match = re.search(r'(\d+)%', like_text)
                if rate_match:
                    like_rate = rate_match.group(1) + "%"

                count_match = re.search(r'\((\d+)\)', like_text)
                if count_match:
                    like_count = int(count_match.group(1))

            views_text = ""
            views_ele = video_ele.find('div', class_=lambda x: x and 'card-mobile-duration' in x and '次' in str(x))
            if views_ele:
                views_text = views_ele.get_text(strip=True)

            studio = {}
            studio_ele = video_ele.find('a', class_=lambda x: x and 'card-mobile-user' in x)
            if studio_ele:
                studio_name = studio_ele.get_text(strip=True)
                studio_url = studio_ele.get('href', '')
                studio_query = studio_url.split("?")[1] if studio_url and "?" in studio_url else ""

                studio = VideoStudio(
                    name=studio_name,
                    query=studio_query
                )

            return VideoPreview(
                video_id=video_id,
                cover_url=img_url,
                title=video_title,
                duration=duration_text,
                view_count=self._parse_views(views_text),
                like_rate=like_rate,
                like_count=like_count,
                studio=studio
            )

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            logger.error(f"提取视频信息错误: {str(e)}")
            return None

    def _extract_based_video_info(self, item: Tag) -> Optional[VideoBase]:
        """从单个 基础视频 元素中提取信息"""
        try:
            video_link = item.find('a', class_=lambda x: x and 'video-link' in x)
            if not video_link:
                video_link = item.find_parent('a')

            href = video_link.get('href', '') if video_link else ''
            rel_video_id = self._extract_video_id(href)
            if not rel_video_id:
                return None

            rel_title = ""
            
            title_selectors = [
                item.find('div', class_=lambda x: x and 'home-rows-videos-title' in x),
                item.find('div', class_=lambda x: x and 'card-mobile-title' in x),
                item.find('div', class_='title'),
                item.find('span', class_='title'),
                item.find('h3'),
                item.find('h4'),
                video_link,
            ]
            
            for title_elem in title_selectors:
                if title_elem:
                    text = title_elem.get_text(strip=True)
                    if text and len(text) > 1:
                        rel_title = text
                        break
            
            if not rel_title:
                img_elem = item.find('img')
                if img_elem:
                    rel_title = img_elem.get('alt', '') or img_elem.get('title', '')

            img_elem = item.find('img')
            rel_cover_url = img_elem.get('src', '') if img_elem else ''

            return VideoBase(
                video_id=rel_video_id,
                title=rel_title,
                cover_url=rel_cover_url,
            )

        except Exception as e:
            logger.exception(f"解析相关视频项错误: {str(e)}")
            return None

    def _extract_search_result_video(self, link_tag: Tag) -> Optional[VideoPreview]:
        """从搜索结果页的 <a> 标签提取视频信息"""
        try:
            href = link_tag.get('href', '')
            video_id = self._extract_video_id(href)
            if not video_id:
                return None

            video_title = ""

            # 尝试多种标题选择器
            title_selectors = [
                link_tag.find('div', class_=lambda x: x and 'home-rows-videos-title' in x),
                link_tag.find('div', class_=lambda x: x and 'card-mobile-title' in x),
                link_tag.find('div', class_=lambda x: x and 'title' in x and 'thumbnail' not in x and 'duration' not in x),
                link_tag.find('span', class_=lambda x: x and 'title' in x),
                link_tag.find('h3'),
                link_tag.find('h4'),
            ]

            for title_elem in title_selectors:
                if title_elem:
                    text = title_elem.get_text(strip=True)
                    if text and len(text) > 1:
                        video_title = text
                        break

            # 回退：从 img 的 alt/title 属性获取标题
            if not video_title:
                img_elem = link_tag.find('img')
                if img_elem:
                    video_title = img_elem.get('alt', '') or img_elem.get('title', '')

            # 如果 <a> 内没找到标题，尝试从父级或兄弟元素查找
            if not video_title:
                parent = link_tag.parent
                if parent:
                    parent_title_selectors = [
                        parent.find('div', class_=lambda x: x and 'home-rows-videos-title' in x),
                        parent.find('div', class_=lambda x: x and 'card-mobile-title' in x),
                        parent.find('div', class_=lambda x: x and 'title' in x and 'thumbnail' not in x and 'duration' not in x),
                        parent.find('span', class_=lambda x: x and 'title' in x),
                    ]
                    for title_elem in parent_title_selectors:
                        if title_elem:
                            text = title_elem.get_text(strip=True)
                            if text and len(text) > 1:
                                video_title = text
                                break

            # 最终回退：使用 video_id 作为标题
            if not video_title:
                video_title = video_id

            img_elem = link_tag.find('img')
            cover_url = img_elem.get('src', '') if img_elem else ''

            return VideoPreview(
                video_id=video_id,
                cover_url=cover_url,
                title=video_title,
            )

        except Exception as e:
            logger.error(f"提取搜索结果视频错误: {str(e)}")
            return None

    def _find_cover_url_from_page(self, soup: BeautifulSoup, video_id: str, page_content: str = '') -> str:
        """
        从视频详情页HTML中查找当前视频的 cover 格式封面海报URL
        关键：cover 图片的文件名可能是数字ID（如407019）也可能是哈希ID（如OmjQkYr），
        所以不能通过文件名匹配 video_id，必须通过 <a href="/watch?v={video_id}"> 定位链接，
        再找链接内的 cover 图片。
        """
        # 方法1：在页面中查找指向当前视频的链接，获取链接内的 cover 图片
        # 这是唯一可靠的方法，因为 cover 文件名可能是哈希ID，不一定等于 video_id
        for link in soup.find_all('a', href=lambda x: x and f'/watch?v={video_id}' in str(x)):
            img = link.find('img', src=lambda x: x and '/image/cover/' in str(x))
            if img:
                cover_src = img.get('src', '')
                if cover_src:
                    logger.info(f"方法1匹配到 cover URL: {cover_src}")
                    return cover_src

        # 调试信息：列出页面中所有 cover 图片
        cover_imgs = soup.find_all('img', src=lambda x: x and '/image/cover/' in str(x))
        cover_filenames = [img.get('src', '').split('/image/cover/')[-1].split('?')[0] for img in cover_imgs[:5]]
        logger.info(f"页面中共有 {len(cover_imgs)} 个 cover 格式图片，但未匹配到 video_id={video_id} 的链接，前5个: {cover_filenames}")

        return ""

    async def _get_cover_from_related_pages(self, current_soup: BeautifulSoup, video_id: str) -> str:
        """
        从相关视频的详情页获取当前视频的 cover 格式封面URL
        原理：当前视频的详情页通常不会链接到自己，但在同系列/相关视频的详情页中，
        当前视频会作为相关视频出现，并带有 /image/cover/ 格式的封面图片。

        关键：cover 文件名可能是哈希ID（如 OmjQkYr），不能用正则匹配 video_id，
        必须用 BeautifulSoup 查找 <a href="/watch?v={video_id}"> 链接内的 cover 图片。

        v3.3.7 修复：之前只遍历前5个相关视频，部分视频（如 39468）要遍历到第6个
        才找到 cover 链接。现在改为遍历所有相关视频（最多 30 个），找到立即返回。
        同时支持 thumbnail 链接→cover 链接的发现（链接中可能同时存在两种图片）。
        """
        try:
            # 从当前页面的 soup 提取相关视频ID（避免重复请求当前页面）
            related_ids = []
            for link in current_soup.find_all('a', href=lambda x: x and '/watch?v=' in str(x)):
                href = link.get('href', '')
                vid = self._extract_video_id(href)
                if vid and vid != video_id and vid not in related_ids:
                    related_ids.append(vid)

            if not related_ids:
                logger.info(f"当前页面未找到相关视频，无法获取 video_id={video_id} 的 cover URL")
                return ""

            # v3.3.7: 扩大遍历范围到 30 个（原来只 5 个，部分视频要遍历到第6个才找到）
            max_check = min(len(related_ids), 30)
            logger.info(f"从当前页面提取到 {len(related_ids)} 个相关视频，将遍历前 {max_check} 个查找 cover")

            # 遍历相关视频的详情页，查找指向当前视频的链接及其 cover 图片
            for related_id in related_ids[:max_check]:
                try:
                    related_page_content = await self.cf_bypasser.get_request(
                        f"{settings.HANIME_BASE_URL}/watch?v={related_id}"
                    )
                    if not related_page_content:
                        continue

                    related_soup = BeautifulSoup(related_page_content, 'lxml')

                    # 查找指向当前视频的链接
                    links_to_current = related_soup.find_all(
                        'a', href=lambda x: x and f'/watch?v={video_id}' in str(x)
                    )
                    for link in links_to_current:
                        # 优先找 cover 图片（竖版海报）
                        img = link.find('img', src=lambda x: x and '/image/cover/' in str(x))
                        if img:
                            cover_src = img.get('src', '')
                            if cover_src:
                                logger.info(f"从相关视频 {related_id} 的详情页找到 cover URL: {cover_src}")
                                return cover_src

                    # v3.3.7 新增：如果该相关视频页面找到了指向当前视频的链接，
                    # 但链接内没有 cover 图片，检查页面中是否有以当前视频 ID 命名的 cover 图片
                    # （源站部分页面的 cover 图片不在 <a> 标签内，而是单独的 <img>）
                    if links_to_current:
                        # 用 video_id 直接拼路径尝试（cover 文件名 = video_id 的情况）
                        direct_cover_url = f"https://vdownload.hembed.com/image/cover/{video_id}.jpg"
                        logger.info(f"相关视频 {related_id} 页面有指向当前视频的链接，尝试直接 cover URL: {direct_cover_url}")
                        # 验证该 URL 是否出现在页面源码中
                        if direct_cover_url in related_page_content or f"/image/cover/{video_id}.jpg" in related_page_content:
                            logger.info(f"✓ 在页面源码中找到 video_id={video_id} 的 cover 图片引用")
                            return direct_cover_url
                except Exception as e:
                    logger.warning(f"获取相关视频 {related_id} 的详情页失败: {e}")
                    continue

            logger.info(f"遍历 {max_check} 个相关视频详情页后，未找到 video_id={video_id} 的 cover URL")
            return ""
        except Exception as e:
            logger.warning(f"从相关视频获取封面失败: {e}")
            return ""

    def _parse_views(self, views_text: str) -> int:
        """解析观看次数文本（兼容繁体萬/千和简体万/千）"""
        if not views_text: return 0
        num_part = views_text
        multiplier = 1
        if "萬" in views_text or "万" in views_text:
            sep = "萬" if "萬" in views_text else "万"
            num_part = views_text.split(sep)[0]
            multiplier = 10000
        elif "千" in views_text:
            num_part = views_text.split("千")[0]
            multiplier = 1000

        try:
            num_str = re.sub(r'[^\d.]', '', num_part)
            if not num_str: return 0
            return int(float(num_str) * multiplier)
        except ValueError:
            views_str_digits = re.sub(r'[^\d]', '', views_text)
            try:
                return int(views_str_digits) if views_str_digits else 0
            except ValueError:
                return 0

    async def get_video_detail(self, video_id: str) -> VideoDetail:
        """获取视频详情"""
        try:
            video_url = f"{settings.HANIME_BASE_URL}/watch?v={video_id}"
            page_content = await self.cf_bypasser.get_request(video_url)

            soup = BeautifulSoup(page_content, 'lxml')

            video_elem = soup.find('video', id='player')
            cover_url = video_elem.get('poster', '') if video_elem else ''

            # 尝试从页面中获取 cover 格式的封面海报URL（竖版，/image/cover/路径）
            # 优先级：cover 格式 > thumbnail/h 格式（poster）
            poster_url = self._find_cover_url_from_page(soup, video_id, page_content)
            if poster_url:
                logger.info(f"从当前页面找到 cover 海报: {poster_url}，替换 poster: {cover_url}")
                cover_url = poster_url
            else:
                # 回退：从相关视频的详情页查找当前视频的 cover URL
                # 当前视频自己的页面通常不会链接到自己，但相关视频页面会链接到当前视频
                try:
                    related_cover = await self._get_cover_from_related_pages(soup, video_id)
                    if related_cover:
                        logger.info(f"从相关视频页面获取到 cover 海报: {related_cover}")
                        cover_url = related_cover
                except Exception as e:
                    logger.warning(f"从相关视频页面获取封面失败: {e}")

            stream_urls_list = self._extract_stream_urls(video_elem)
            if not stream_urls_list:
                stream_urls_list = self._extract_stream_urls_from_js(page_content)
            default_video_url = stream_urls_list[0].url if stream_urls_list else ""

            video_studio = self._extract_studio_info(soup)

            video_type_ele = soup.find(id='video-artist-name')
            video_type_ele = video_type_ele.find_next_sibling('a') if video_type_ele else None
            video_type_name = video_type_ele.get_text(strip=True) if video_type_ele else ''
            video_type_url = video_type_ele.get('href', '') if video_type_ele else ''
            video_type_query = video_type_url.split("?")[1] if video_type_url and "?" in video_type_url else ""

            video_type = VideoType(
                name=to_simplified(video_type_name),
                query=to_simplified(video_type_query)
            )

            video_title_ele = soup.find(id='shareBtn-title')
            video_title = video_title_ele.get_text(strip=True) if video_title_ele else ''

            description_wrapper_elem = soup.find('div', class_=lambda x: x and 'video-description-panel' in x)

            # 遍历所有直接子 div，找到包含 "次" 和日期的那个
            views_match = None
            views_str = ""
            upload_date_str = ""
            subtitle = ""
            description = ""

            if description_wrapper_elem:
                child_divs = description_wrapper_elem.find_all('div', recursive=False)
                for child_div in child_divs:
                    child_text = child_div.get_text(strip=True)
                    # 匹配 "XXX次  YYYY-MM-DD" 格式
                    match = re.search(r'(\d+(?:\.\d+)?(?:萬|万|千)?)次\s+(\d{4}-\d{2}-\d{2})', child_text)
                    if match:
                        views_match = match
                        views_str = match.group(1)
                        upload_date_str = match.group(2)
                        break

                # subtitle: 不包含观看次数的子div中，取非描述性的短文本
                for child_div in child_divs:
                    child_text = child_div.get_text(strip=True)
                    # 跳过包含观看次数的 div 和过长的描述文本
                    if '次' in child_text and re.search(r'\d{4}-\d{2}-\d{2}', child_text):
                        continue
                    if len(child_text) > 200:
                        continue
                    # 跳过仅包含上传者信息的 div（通常以"上傳者"结尾）
                    if child_text.endswith('上傳者') or child_text.endswith('上传者'):
                        continue
                    # 第一个符合条件的短文本作为 subtitle
                    subtitle = child_text
                    break

                # description: 最长的子div文本
                for child_div in child_divs:
                    child_text = child_div.get_text(strip=True)
                    if len(child_text) > len(description) and not (child_text.endswith('上傳者') or child_text.endswith('上传者')):
                        # 排除观看次数行
                        if not ('次' in child_text and re.search(r'\d{4}-\d{2}-\d{2}', child_text) and len(child_text) < 50):
                            description = child_text

            # v3.5.1: 提取点赞率 like_rate
            # 详情页的点赞率可能出现在多个位置，按优先级尝试提取
            like_rate = ""
            # 策略1: 查找 stats-container / stat-item（与列表页一致的结构）
            stats_container = soup.find('div', class_=lambda x: x and 'stats-container' in x)
            if stats_container:
                stat_items = stats_container.find_all('div', class_=lambda x: x and 'stat-item' in x)
                if stat_items:
                    like_text = stat_items[0].get_text(strip=True)
                    rate_match = re.search(r'(\d+%)', like_text)
                    if rate_match:
                        like_rate = rate_match.group(1)
            # 策略2: 查找包含 thumb_up 的元素
            if not like_rate:
                thumb_up_elem = soup.find('div', class_=lambda x: x and 'thumb_up' in str(x) if x else False)
                if thumb_up_elem:
                    like_text = thumb_up_elem.get_text(strip=True)
                    rate_match = re.search(r'(\d+)%', like_text)
                    if rate_match:
                        like_rate = rate_match.group(1) + "%"
            # 策略3: 查找点赞按钮区域的百分比文本（video-info 或 video-action 区域）
            if not like_rate:
                like_btn_area = soup.find('div', class_=lambda x: x and ('video-action' in str(x) or 'like-button' in str(x) or 'action-bar' in str(x)) if x else False)
                if like_btn_area:
                    like_text = like_btn_area.get_text(strip=True)
                    rate_match = re.search(r'(\d+)%', like_text)
                    if rate_match:
                        like_rate = rate_match.group(1) + "%"
            # 策略4: 在页面全部文本中，查找点赞相关的百分比（更宽松的兜底）
            if not like_rate:
                # 查找包含 "thumb_up" 或 "good" class 的父元素中的百分比
                for elem in soup.find_all(class_=lambda x: x and ('thumb' in str(x) or 'like' in str(x) or 'good' in str(x))):
                    like_text = elem.get_text(strip=True)
                    rate_match = re.search(r'(\d+)%', like_text)
                    if rate_match:
                        like_rate = rate_match.group(1) + "%"
                        break

            tags = self._extract_tags(soup)

            series_videos = self._extract_series_videos(soup)

            basic_related_videos = self._extract_related_videos_based(soup)
            detailed_related_videos = self._extract_related_videos_detailed(soup)

            upload_date_value = None
            if upload_date_str:
                try:
                    upload_date_value = datetime.strptime(upload_date_str, '%Y-%m-%d').date()
                except ValueError:
                    upload_date_value = None

            video_detail = VideoDetail(
                video_id=video_id,
                title=video_title,
                subtitle=to_simplified(subtitle),
                cover_url=cover_url,
                description=to_simplified(description),
                default_video_url=default_video_url,
                stream_urls=stream_urls_list,
                view_count=self._parse_views(views_str),
                like_rate=like_rate,
                upload_date=upload_date_value,
                studio=video_studio,
                video_type=video_type,
                tags=tags,
                series_videos=series_videos,
                basic_related_videos=basic_related_videos,
                detailed_related_videos=detailed_related_videos
            )

            return video_detail

        except Exception as e:
            logger.error(f"获取视频详情错误: {str(e)}")
            raise

    async def get_video_comments(self, video_id: str) -> List[VideoComment]:
        """获取视频播放评论"""
        try:
            video_load_comment_url = f"{settings.HANIME_BASE_URL}/loadComment"
            params = {
                "id": video_id,
                "type": "video",
                "content": "comment-tablink"
            }
            respond = await self.cf_bypasser.get_request(video_load_comment_url, params=params)
            page_content = json.loads(respond).get("comments", "")

            page_content = f"<html>{page_content}</html>"
            soup = BeautifulSoup(page_content, 'lxml')

            if not soup:
                logger.error("解析评论错误: 无法获取评论元素")
                return []

            video_comments = []
            comment_elements = soup.find_all(id=lambda x: x and 'comment-like-form-wrapper' in str(x))

            for comment_elem in comment_elements:
                try:
                    comment_id = ""
                    load_replies_btn = comment_elem.find('div', attrs={'data-commentid': True})
                    if load_replies_btn:
                        comment_id = load_replies_btn.get('data-commentid', '')

                    user_avatar_ele = comment_elem.find_previous_sibling('a')
                    user_avatar_ele = user_avatar_ele.find('img') if user_avatar_ele else None
                    user_avatar = user_avatar_ele.get('src', '') if user_avatar_ele else ''

                    username_ele = comment_elem.find_previous_sibling('div')
                    if username_ele:
                        username_ele = username_ele.find('div', class_=lambda x: x and 'comment-index-text' in x)
                        username_ele = username_ele.find('a') if username_ele else None

                    username_time_text = username_ele.get_text(strip=True) if username_ele else ""

                    username = ""
                    comment_time = ""
                    if username_time_text:
                        match = re.match(r'(.+?)(?:\s+(\d+.+))?$', username_time_text)
                        if match:
                            username = match.group(1).strip()
                            comment_time = match.group(2).strip() if match.group(2) else ""

                    if not comment_time and username_ele:
                        time_ele = username_ele.find('span')
                        comment_time = time_ele.get_text(strip=True) if time_ele else ""

                    comment_content_ele = comment_elem.find_previous_sibling('div')
                    if comment_content_ele:
                        comment_content_ele = comment_content_ele.find_all('div', class_=lambda x: x and 'comment-index-text' in x)
                        comment_content_ele = comment_content_ele[1] if len(comment_content_ele) > 1 else None

                    comment_content = comment_content_ele.get_text(strip=True) if comment_content_ele else ''

                    like_count = 0
                    like_ele = comment_elem.find('div', text=lambda x: x and 'thumb_up' in str(x))
                    if like_ele:
                        like_span = like_ele.find('span')
                        if like_span:
                            like_text = like_span.get_text(strip=True)
                            try:
                                like_count = int(re.search(r'\d+', like_text).group()) if re.search(r'\d+', like_text) else 0
                            except:
                                like_count = 0

                    reply_count = 0
                    reply_btn = comment_elem.find('div', class_=lambda x: x and 'load-replies-btn' in x)
                    if reply_btn:
                        reply_text = reply_btn.get_text(strip=True)
                        try:
                            digits = re.findall(r'\d+', reply_text)
                            reply_count = int(digits[0]) if digits else 0
                        except:
                            reply_count = 0

                    comment = VideoComment(
                        comment_id=comment_id,
                        user_avatar=user_avatar,
                        username=username,
                        comment_time=comment_time,
                        comment_content=comment_content,
                        like_count=like_count,
                        reply_count=reply_count
                    )
                    video_comments.append(comment)

                except Exception as e:
                    logger.error(f"解析评论错误: {str(e)}")

            return video_comments
        except Exception as e:
            logger.error(f"获取视频评论错误: {str(e)}")
            raise

    async def get_comment_replies(self, comment_id: str) -> List[CommentReply]:
        """获取视频评论的相关回复"""
        try:
            video_load_comment_url = f"{settings.HANIME_BASE_URL}/loadReplies"
            params = {
                "id": comment_id
            }
            respond = await self.cf_bypasser.get_request(video_load_comment_url, params=params)
            page_content = json.loads(respond).get("replies", "")

            page_content = f"<html>{page_content}</html>"
            soup = BeautifulSoup(page_content, 'lxml')

            if not soup:
                logger.error("解析评论回复错误: 无法获取评论元素")
                return []

            replies_list = []
            reply_root = soup.find(id=f'reply-start-{comment_id}')

            if not reply_root:
                logger.error(f"未找到评论回复的根元素: reply-start-{comment_id}")
                return []

            all_divs = reply_root.find_all('div', recursive=False)

            for i in range(0, len(all_divs), 2):
                try:
                    if i + 1 >= len(all_divs):
                        break

                    content_div = all_divs[i]
                    like_div = all_divs[i + 1]

                    user_avatar_ele = content_div.find('img', class_=lambda x: x and 'img-circle' in x)
                    user_avatar = user_avatar_ele.get('src', '') if user_avatar_ele else ''

                    user_info_div = content_div.find('div', class_=lambda x: x and 'comment-index-text' in x)
                    user_info_ele = user_info_div.find('a') if user_info_div else None
                    username_time_text = user_info_ele.get_text(strip=True) if user_info_ele else ""

                    username = ""
                    reply_time = ""
                    if username_time_text:
                        match = re.match(r'(.+?)(?:\s+(\d+.+))?$', username_time_text)
                        if match:
                            username = match.group(1).strip()
                            reply_time = match.group(2).strip() if match.group(2) else ""

                    if not reply_time and user_info_ele:
                        time_ele = user_info_ele.find('span')
                        reply_time = time_ele.get_text(strip=True) if time_ele else ""

                    content_ele_list = content_div.find_all('div', class_=lambda x: x and 'comment-index-text' in x)
                    content_ele = content_ele_list[1] if len(content_ele_list) > 1 else None
                    reply_content = content_ele.get_text(strip=True) if content_ele else ''

                    like_count = 0
                    like_span = like_div.find('div')
                    if like_span:
                        like_span = like_span.find('span')
                        if like_span:
                            like_text = like_span.get_text(strip=True)
                            display_style = like_span.get('style', '')
                            if display_style and "display:none" in display_style:
                                like_count = 0
                            else:
                                try:
                                    like_count = int(like_text) if like_text else 0
                                except:
                                    digits = re.findall(r'-?\d+', like_text)
                                    like_count = int(digits[0]) if digits else 0

                    reply = CommentReply(
                        user_avatar=user_avatar,
                        username=username,
                        reply_time=reply_time,
                        reply_content=reply_content,
                        like_count=like_count
                    )
                    replies_list.append(reply)

                except Exception as e:
                    logger.exception("提取评论回复信息错误")
                    continue

            return replies_list

        except Exception as e:
            logger.exception("获取视频评论回复错误")
            raise

    def _extract_video_id(self, url: str) -> str:
        """从URL中提取视频ID"""
        if not url: return ""
        match = re.search(r'[?&]v=([^&]+)', url)
        return match.group(1) if match else ""

    def _extract_video_id_from_image(self, url: str) -> str:
        """从图片URL中提取视频ID"""
        if not url: return ""
        match = re.search(r'/image/thumbnail/(\d+)', url)
        return match.group(1) if match else ""

    def _extract_video_id_from_url(self, video_url: str) -> str:
        """从视频URL中提取视频ID"""
        if not video_url: return ""
        match = re.search(r'/watch\?v=([^&]+)', video_url)
        return match.group(1) if match else ""

    def _extract_tags(self, soup: BeautifulSoup) -> List[VideoTag]:
        """提取视频标签信息"""
        tags = []
        tag_elements = soup.find_all('a', class_=lambda x: x and 'single-video-tag' in str(x), href=lambda x: x and 'tags' in str(x))
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text(strip=True) if tag_elem else ""
            tag_name = re.sub(r'\s*\(\d+\)$', '', tag_text)

            href = tag_elem.get('href', '') if tag_elem else ""
            tag_search_query = href.split("?")[1] if href and "?" in href else ""
            tag_search_query = tag_search_query.replace("%5B%5D", "")
            if tag_name:
                tags.append(
                    VideoTag(
                        name=to_simplified(tag_name),
                        query=to_simplified(tag_search_query)
                    )
                )
        return tags

    def _extract_stream_urls(self, video_elem: Tag) -> List[VideoStreamUrl]:
        """提取视频流URL信息"""
        stream_urls_list = []
        source_elements = video_elem.find_all('source') if video_elem else []
        for source_ele in source_elements:
            source_url = source_ele.get('src', '')
            if not source_url:
                continue
            size = source_ele.get('size', '') + "p" if source_ele.get('size') else "unknown"

            stream_urls_list.append(
                VideoStreamUrl(
                    quality=size,
                    url=source_url
                ))
        return stream_urls_list

    def _extract_stream_urls_from_js(self, page_content: str) -> List[VideoStreamUrl]:
        """从JavaScript中提取视频流URL"""
        stream_urls_list = []
        
        patterns = [
            r'hls_url["\']?\s*:\s*["\']([^"\']+)["\']',
            r'mp4_url["\']?\s*:\s*["\']([^"\']+)["\']',
            r'source["\']?\s*:\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
            r'video_url["\']?\s*:\s*["\']([^"\']+)["\']',
            r'play_url["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"url"\s*:\s*"([^"]+\.(?:mp4|m3u8))"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_content)
            for url in matches:
                if url and url not in [s.url for s in stream_urls_list]:
                    if '.m3u8' in url.lower():
                        quality = 'HLS'
                    elif '.mp4' in url.lower():
                        quality = 'MP4'
                    else:
                        quality = 'unknown'
                    stream_urls_list.append(
                        VideoStreamUrl(
                            quality=quality,
                            url=url
                        ))

        return stream_urls_list

    def _extract_studio_info(self, soup: BeautifulSoup) -> VideoStudio:
        """提取视频发行商信息"""
        studio_img_ele = soup.find(id='video-user-avatar')
        studio_img_ele = studio_img_ele.find_next_sibling('img') if studio_img_ele else None
        
        studio_name_ele = soup.find(id='video-artist-name')

        studio_icon_url = studio_img_ele.get('src', '') if studio_img_ele else ''
        studio_name = studio_name_ele.get_text(strip=True) if studio_name_ele else ''
        studio_url = studio_name_ele.get('href', '') if studio_name_ele else ''
        studio_query = studio_url.split("?")[1] if studio_url and "?" in studio_url else ""

        return VideoStudio(
            name=studio_name,
            icon_url=studio_icon_url,
            url=studio_url,
            query=studio_query
        )

    def _extract_related_videos_based(self, soup: BeautifulSoup) -> List[VideoBase]:
        """提取相关视频信息"""
        related_videos = []
        related_items = soup.find_all('div', class_=lambda x: x and 'home-rows-videos-div' in str(x))

        for item in related_items:
            video_info = self._extract_based_video_info(item)
            if video_info:
                related_videos.append(video_info)

        return related_videos

    def _extract_related_videos_detailed(self, soup: BeautifulSoup) -> List[VideoPreview]:
        """提取相关视频信息"""
        related_videos = []
        related_items = soup.find_all('div', class_=lambda x: x and 'related-doujin-videos' in str(x))

        for video_ele in related_items:
            video_info = self._extract_detailed_video_info(video_ele)
            if video_info:
                related_videos.append(video_info)

        return related_videos

    def _extract_series_videos(self, soup: BeautifulSoup) -> List[VideoPreview]:
        """提取系列视频信息"""
        series_videos = []
        series_items = soup.find_all('div', class_=lambda x: x and 'multiple-link-wrapper' in str(x))

        for video_ele in series_items:
            video_info = self._extract_detailed_video_info_old(video_ele)
            if video_info:
                series_videos.append(video_info)

        return series_videos

    async def get_calendar_data(self) -> CalendarData:
        """获取日历/新番列表数据 - 通过搜索 API 构建各类型最新番剧"""
        try:
            genres = ["裏番", "泡麵番", "Motion Anime", "3DCG", "2.5D", "2D動畫", "AI生成", "MMD", "Cosplay"]
            calendar_data = CalendarData()

            for genre in genres:
                try:
                    search_result = await self.search_videos(
                        query=None, genre=genre, tags=None, broad=None,
                        sort="最新上市", year=None, month=None, page=1
                    )
                    # 取前10个视频
                    videos = search_result.detailed_videos[:10] if search_result.detailed_videos else []
                    day_data = CalendarDay(
                        day_of_week=to_simplified(genre),
                        date=to_simplified(genre),
                        videos=videos
                    )
                    calendar_data.days.append(day_data)
                except Exception as e:
                    logger.warning(f"获取 {genre} 新番数据失败: {str(e)}")
                    calendar_data.days.append(CalendarDay(day_of_week=to_simplified(genre), date=to_simplified(genre), videos=[]))

            return calendar_data

        except Exception as e:
            logger.exception(f"获取日历数据错误: {str(e)}")
            raise

    async def get_search_combination(self) -> SearchCombination:
        """获取搜索组合"""
        try:
            search_combination_url = f"{settings.HANIME_BASE_URL}/search"
            page_content = await self.cf_bypasser.get_request(search_combination_url)

            soup = BeautifulSoup(page_content, 'lxml')

            video_types_eles = soup.select("#genre-modal .hentai-sort-options")
            video_types = [ele.get_text(strip=True) for ele in video_types_eles]

            tags_dict = {}
            all_elements = soup.select("#tags .modal-body h5, #tags .modal-body label")

            current_category = None
            current_tags = []

            for element in all_elements:
                tag_name = element.name

                if tag_name == "h5":
                    if current_category and current_tags:
                        tags_dict[current_category] = current_tags
                    current_category = element.get_text(strip=True)
                    current_tags = []
                elif tag_name == "label" and current_category:
                    tag_text = element.get_text(strip=True)
                    if tag_text:
                        current_tags.append(tag_text)

            if current_category and current_tags:
                tags_dict[current_category] = current_tags

            sort_by_eles = soup.select("#sort-modal .hentai-sort-options")
            sort_by_options = [ele.get_text(strip=True) for ele in sort_by_eles]

            return SearchCombination(
                video_types=convert_list(video_types),
                tags=convert_dict(tags_dict),
                sort=convert_list(sort_by_options)
            )

        except Exception as e:
            logger.exception(f"获取搜索组合错误: {str(e)}")
            raise

    async def search_videos(self,
                            query: Optional[str],
                            genre: Optional[str],
                            tags: Optional[List[str]],
                            broad: Optional[bool],
                            sort: Optional[str],
                            year: Optional[int],
                            month: Optional[int],
                            page: int
                            ) -> SearchResults:
        """搜索视频"""
        try:
            search_url = f"{settings.HANIME_BASE_URL}/search"

            params = {}

            if query:
                params["query"] = query

            if genre:
                params["genre"] = genre

            if tags and len(tags) > 0:
                for i, tag in enumerate(tags):
                    params[f"tags[{i}]"] = tag

            if sort:
                params["sort"] = sort

            if page > 1:
                params["page"] = str(page)

            if broad:
                params["broad"] = "on"

            if year:
                params["year"] = year

            if month:
                params["month"] = month

            page_content = await self.cf_bypasser.get_request(search_url, params=params)

            if not page_content:
                raise Exception("搜索视频失败: 无法获取页面内容")

            soup = BeautifulSoup(page_content, 'lxml')

            pages_ele = soup.find('ul', class_='pagination')
            total_pages = 0
            has_next = False

            if pages_ele:
                li_elements = pages_ele.find_all('li')
                if len(li_elements) >= 2:
                    last_page_li = li_elements[-2]
                    total_pages = int(last_page_li.get_text(strip=True)) if last_page_li.get_text(strip=True).isdigit() else 0

                if total_pages > page:
                    has_next = True

            # 搜索结果页视频提取 - 使用多种选择器兼容不同页面结构
            basic_video_list = []

            # 方式1: 搜索结果页标准结构 <a href="/watch?v=xxx"> + div.home-rows-videos-div
            wrapper = soup.find('div', id='home-rows-wrapper')
            if wrapper:
                video_links = wrapper.find_all('a', href=lambda x: x and '/watch?v=' in str(x))
                for link in video_links:
                    video_info = self._extract_search_result_video(link)
                    if video_info:
                        basic_video_list.append(video_info)

            # 方式2: 首页风格的 div[title] 结构（兼容旧版）
            if not basic_video_list:
                video_elements = soup.select('#home-rows-wrapper div[title]')
                if video_elements:
                    for video_ele in video_elements:
                        video_info = self._extract_detailed_video_info(video_ele)
                        if video_info:
                            basic_video_list.append(video_info)

            # 方式3: video-item-container 结构（兼容旧版）
            if not basic_video_list:
                video_elements = soup.select('#home-rows-wrapper [class*="video-item-container"]')
                if video_elements:
                    for video_ele in video_elements:
                        video_info = self._extract_based_video_info(video_ele)
                        if video_info:
                            basic_video_list.append(video_info)

            return SearchResults(
                total_pages=total_pages,
                page=page,
                basic_videos=[],
                detailed_videos=basic_video_list,
                has_next=has_next
            )

        except Exception as e:
            logger.exception(f"搜索视频错误: {str(e)}")
            raise