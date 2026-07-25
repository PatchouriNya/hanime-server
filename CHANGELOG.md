# 更新日志

## v3.2.5 (2026-07-25)

### 修复

1. **修复刮削时 video_id 提取失败导致 NFO 内容缺失**：
   - 根因：重命名后的文件名（如"欢迎光临！水龙敬乐园 - S01E01 - 第 1 集.mp4"）无法通过正则匹配提取出 video_id
   - 修复：新增从同名 NFO 文件和数据库下载记录中回退查找 video_id 的逻辑
   - 改进 `_extract_video_id` 支持"番剧名 - S01E01 - 第 N 集"格式返回空字符串触发回退查找
   - 新增 `_lookup_video_id_from_nfo` 方法从现有 NFO 的 uniqueid 标签读取 video_id
   - 新增 `_lookup_video_id_from_db` 方法从数据库下载记录中匹配 video_id

2. **修复刮削后文件名和 NFO 标题包含年份后缀**：
   - 根因：`series_name` 来自目录名（如"欢迎光临！水龙敬乐园 (2017)"），被直接用作文件名和 NFO 标题
   - 修复：文件名和 NFO 标题统一去除年份后缀，年份仅保留在目录名中
   - tvshow.nfo 的 title/originaltitle 现在是"欢迎光临！水龙敬乐园"而非"欢迎光临！水龙敬乐园 (2017)"

3. **修复刮削重命名时残留旧附属文件**：
   - 根因：视频文件重命名时，同名的旧 NFO/JPG 文件未被清理
   - 修复：重命名视频文件前自动删除同名的 .nfo/.jpg/.png/.webp 文件

## v3.2.3 (2026-07-25)

### 修复

1. **下载时自动检测同系列番剧并合并目录**：
   - 下载时自动从源站读取 series_videos 信息，检测同系列已下载的番剧
   - 如果第一部已下载（如"不潔之星・赤"），第二部下载时自动放入同一目录的 Season 2
   - 自动将第一部已有视频整理到 Season 1 目录
   - 自动将目录名重命名为系列基础名（去掉编号后缀，如"不潔之星・赤"→"不潔之星"）
   - 更新所有相关数据库记录的文件路径

## v3.2.2 (2026-07-25)

### 新增

1. **系列合并功能**：
   - 视频详情页系列影片区域新增"合并到系列"按钮，当当前视频和至少一个系列视频都已下载时显示
   - 点击后调用后端系列检测接口，展示合并计划（番剧名称、下载状态、季号），支持编辑系列名称和调整季号
   - 下载管理页面新增"合并系列"按钮，可选择两个或更多已下载的番剧合并到同一系列
   - 合并对话框支持选择番剧、设置系列名称、分配季号
   - 后端API：`POST /downloads/series/detect`（检测系列信息）和 `POST /downloads/series/merge`（执行合并）
   - 系列名自动提取：从标题中去掉编号后缀（如"不潔之星・赤"→"不潔之星"、"某番剧 2"→"某番剧"）

2. **刮削多季支持**：
   - 刮削服务新增多季识别：自动从 Season 子目录名解析季号（Season 1 → 第1季，Season 2 → 第2季）
   - 每季独立编号集号（Season 1 从 E01 开始，Season 2 也从 E01 开始）
   - 为每个 Season 目录生成独立的 `season.nfo`
   - 为每个 Season 目录复制 `poster.jpg` 并生成 `season{NN}-poster.jpg`
   - 重命名文件时保留在各 Season 目录内，使用正确的 S02E01 格式

## v3.2.1 (2026-07-25)

### 修复

1. **修复删除下载记录时无法删除刮削后重命名的文件**：
   - 根因：刮削服务会将视频文件从 `series_name/video_id_subtitle.mp4` 重命名为 `series_name/Season 1/series_name - S01E01 - 第 1 集.mp4`，但删除时只查找原始路径，导致文件找不到而未被删除
   - 修复：`_delete_video_and_scrape_files` 方法改为先尝试删除原始路径文件，再通过 NFO 中的 `<uniqueid type="hanime" default="true">video_id</uniqueid>` 递归搜索番剧目录定位刮削后的文件
   - 新增 `_find_nfo_by_video_id` 辅助方法：递归搜索番剧目录，匹配 NFO 中的 uniqueid 标签
   - 删除范围扩展：匹配的 NFO 文件 + 同名视频文件（.mp4/.mkv/.avi/.wmv/.flv/.ts）+ 同名缩略图 .jpg + 番剧根目录 video_id.jpg 封面

2. **扫描恢复功能增加清理无效记录**：
   - 新增第二阶段逻辑：检查所有已完成的下载记录，如果对应文件在原始路径和刮削后路径（通过 NFO 查找）都不存在，则自动删除数据库记录
   - 返回值新增 `removed` 列表和 `total_removed` 计数
   - 前端提示信息同步更新，显示恢复和清理的数量

3. **菜单'喜欢的影片'改为'收藏的番剧'**：
   - 侧边栏菜单和收藏页面标题统一更名为"收藏的番剧"

## v3.2.0 (2026-07-25)

### 修复

1. **修复视频详情页日期解析失败的问题**：
   - 根因：源站页面结构中"观看次数+日期"不一定在第一个子div中（如 video_id=13405，第一个div是上传者信息"基佬人13上傳者"），旧代码 `find('div')` 只取第一个div导致正则匹配失败
   - 修复：遍历所有子div查找包含"次+日期"格式的元素
   - 影响范围：所有上传者信息出现在观看次数之前的视频页面

2. **修复副标题被错误解析为"观看次数"的问题**：
   - 之前 `find_all('div')[1]` 取第二个div作为 subtitle，当上传者信息占第一个div时，第二个div是"观看次数+日期"
   - 修复：智能识别 subtitle，跳过包含观看次数的div和上传者信息div

## v3.1.9 (2026-07-25)

### 修复

1. **彻底修复绿联影视中心显示 1970 年的问题**：
   - NFO 写入时自动移除空日期标签（`<year/>`、`<premiered/>`、`<releasedate/>`、`<aired/>`、`<enddate/>`）
   - 防止未来刮削仍产生空标签

### 新增

1. **修复NFO工具**：
   - 下载管理页面新增"修复NFO"按钮
   - 一键扫描所有已有 NFO 文件并移除空日期标签
   - 后端新增 `POST /scrape/fix-nfo` 接口
   - 修复后绿联影视中心不再显示 1970-01-01

## v3.1.8 (2026-07-25)

### 修复

1. **修复绿联影视中心显示 1970 年的问题**：
   - 根因：NFO 文件中当日期字段值为空时，仍创建了空标签（如 `<premiered/>`、`<year/>`、`<aired/>`）
   - 绿联影视中心将空标签解析为 Unix 纪元 1970-01-01
   - 修复：日期值为空时不再创建对应 XML 标签
   - 涉及 6 处：tvshow.nfo 的 year/premiered/releasedate、episode.nfo 的 year/aired、movie.nfo 的 year/premiered/releasedate

## v3.1.7 (2026-07-25)

### 新增

1. **预览图从视频真实画面截取**：
   - 刮削时 `backdrop.jpg`、`landscape.jpg`、单集缩略图优先从已下载的视频文件用 ffmpeg 截取真实画面
   - 不再使用源站预览图作为横版背景图，海报（poster.jpg）仍使用源站竖版封面
   - `backdrop.jpg` 取视频 50% 位置画面（1920x1080）
   - `landscape.jpg` 取视频 70% 位置画面（1000x562），与 backdrop 画面不重复
   - 单集缩略图从同名视频文件 50% 位置截取（1920x1080）
   - `fanart.jpg` / `thumb.jpg` / `banner.jpg` 自动跟随 backdrop / landscape
   - 回退策略：视频文件不存在时仍使用源站 thumbnail URL → poster 裁剪

### 优化

1. **Docker 镜像集成 ffmpeg**：
   - 基础镜像（python:3.10-alpine）新增 ffmpeg 安装，支持视频截帧功能

## v3.1.6 (2026-07-25)

### 修复

1. **修复 download.ts 类型推断错误**：
   - 将速度平滑处理器（`DownloadSpeedSmoother` 单例）从 Pinia 响应式 `state` 移至模块级变量 `_speedSmoother`
   - 根因：类实例放入 `state` 会导致 TypeScript 无法正确推断 store 的 `this` 类型，报错"类型上不存在属性 downloads"
   - 同步修改 actions 中所有 `this.speedSmoother` 引用为 `_speedSmoother`（共3处）

### 清理

1. **删除根目录无用测试文件**：
   - 移除 `test_cover.py` ~ `test_cover5.py` 共5个封面下载调试脚本

## v3.1.5 (2026-07-25)

### 新增

1. **下载管理批量删除功能**：
   - 下载管理页面新增"批量删除"按钮，点击进入批量删除模式
   - 批量模式下可勾选多条下载记录，支持"全选当前列表"和"取消选择"
   - 批量删除确认对话框，可选是否删除源文件
   - 后端新增 `POST /downloads/batch-delete` 接口，支持批量删除

2. **删除时可选是否删除源文件**：
   - **删除源文件**：删除视频文件 + 刮削生成的 NFO 元数据 + 封面/缩略图等图片文件
   - **仅删除记录**：只删除数据库记录，保留所有文件
   - 智能清理：当番剧目录下所有视频文件被删除后，自动删除整个番剧目录（包括所有 NFO 和图片）
   - 后端 `delete_download` 方法新增 `delete_files` 参数，`DownloadAction` 模型新增 `delete_files` 字段

### 优化

1. **视频详情页手机端按钮对齐优化**：
   - 修复 480px 断点下 `.video-actions .el-button` 缺少 `min-width: 0` 和 `justify-content: center` 导致的按钮宽度不一致问题
   - 新增 `align-items: center` 确保按钮内容垂直居中
   - 设置固定 `height`（768px: 36px, 480px: 34px）保证每行按钮等高对齐
   - 添加 `white-space: nowrap` 防止按钮内文字换行
   - 统一图标和文字间距（`margin-left: 4px`）
   - 添加 `margin-left: 0` 移除 el-button 默认间距影响布局

2. **下载管理手机端操作按钮布局优化**：
   - 768px 断点下 left-actions 从 4 列改为 3 列网格，适配新增的"批量删除"按钮
   - 480px 断点下保持 2 列网格
   - 批量操作栏在手机端自动切换为垂直布局

## v3.1.4 (2026-07-25)

### 优化

1. **NFO 字段顺序完全对齐绿联4800plus 参考格式**（参考"Y:\links\电视剧\日番\未来日记 (2011)"）：
   - **tvshow.nfo**：调整字段顺序为 plot→outline→lockdata→dateadded→title→originaltitle→rating→year→sorttitle→mpaa→premiered→releasedate→enddate→runtime→country→genre→studio→uniqueid→episodeguide→id→season(-1)→episode(-1)→displayorder→status
   - **episode.nfo**：调整字段顺序为 plot→outline→lockdata→dateadded→title→rating→year→sorttitle→runtime→uniqueid→episode→season→aired（注意 episode 在 season 之前，对齐参考格式）
   - **movie.nfo**：调整字段顺序为 plot→outline→lockdata→dateadded→title→originaltitle→rating→year→sorttitle→mpaa→premiered→releasedate→runtime→country→genre→studio→uniqueid→id

2. **新增关键字段**：
   - tvshow.nfo 新增 `enddate`（最新集日期）、`episodeguide`、`id`、`season(-1)`、`episode(-1)`、`displayorder(aired)`
   - episode.nfo 新增 `uniqueid`（基于 video_id）
   - movie.nfo 新增 `id` 字段

3. **runtime 时长准确解析**：
   - 新增 `_parse_duration_to_minutes` 方法，从源站 duration 字符串（如 "23:45"）解析为分钟数（向上取整到 24）
   - 支持 HH:MM:SS / MM:SS / 带单位数字 / 纯数字四种格式
   - 新增 `_extract_runtime_minutes` 方法，从元数据列表提取时长
   - tvshow/episode/movie NFO 的 runtime 字段均改为从 duration 解析，不再固定 24 分钟

4. **新增 season01-poster.jpg 文件**：
   - 参考格式"未来日记 (2011)"根目录包含 season01-poster.jpg
   - 自动从根目录 poster.jpg 复制生成，绿联NAS通过此文件识别第1季海报
   - 新增常量 `SEASON_POSTER_FILENAME_PATTERN = "season{:02d}-poster.jpg"`

5. **mpaa 分级调整**：
   - 从 NC-17 改为 TV-MA（对齐参考格式"未来日记"）
   - TV-MA 是电视节目分级，更适合番剧类型

6. **`_find_existing_cover` 排除规则增强**：
   - 新增正则排除 `season\d+-poster\.(jpg|png|webp)` 模式
   - 避免误将 season01-poster.jpg 识别为已有封面导致跳过下载

## v3.1.3 (2026-07-25)

### 优化

1. **Season 目录命名对齐参考格式**：
   - `Season 01` → `Season 1`（不带前导零，对齐 Y:\links 参考格式）
   - 文件名中的 `S01E01` 格式保持不变（仍带前导零）

2. **图片质量全面提升**：
   - 新增 `_get_horizontal_thumbnail_url` 方法，从 cover URL 推导横版缩略图 URL（/image/cover/ → /image/thumbnail/）
   - **backdrop.jpg**：改用 thumbnail URL 下载原生横版 1024x576 图片，放大到 1920x1080（之前从 268x394 竖版 poster 裁剪，画质极差）
   - **fanart.jpg**：同 backdrop，优先复制 backdrop，回退用 thumbnail URL 下载
   - **landscape.jpg**：改用 thumbnail URL 下载，调整到标准尺寸 1000x562
   - **thumb.jpg**：优先复制 landscape，回退用 thumbnail URL 下载
   - **banner.jpg**：长宽比从 16:9 修正为 5.4:1（1000x185），从横版图裁剪中部横条
   - **poster.jpg**：下载后用 PIL LANCZOS 重采样放大到标准尺寸 1000x1426
   - **单集缩略图**：优先用 thumbnail URL 下载横版，放大到 1920x1080

3. **新增图片处理方法**：
   - `_crop_banner_from_landscape`：从横版图裁剪 5.4:1 banner
   - `_upscale_to_standard`：仅放大不缩小，比例不一致时先裁剪
   - `_resize_to_standard`：强制调整到目标尺寸（裁剪+缩放）

4. **日期处理更健壮**：
   - `isinstance(upload_date, datetime)` → `isinstance(upload_date, (datetime, date))`
   - 同时兼容 `date` 对象和 `datetime` 对象（video_service 返回的是 `date` 对象）
   - 所有 NFO 中的 year/premiered/releasedate/aired 字段处理统一

5. **新增常量**：
   - `POSTER_STANDARD_WIDTH/HEIGHT` = 1000x1426
   - `BACKDROP_STANDARD_WIDTH/HEIGHT` = 1920x1080
   - `LANDSCAPE_STANDARD_WIDTH/HEIGHT` = 1000x562
   - `BANNER_STANDARD_WIDTH/HEIGHT` = 1000x185
   - `COVER_URL_PATH` / `THUMBNAIL_URL_PATH` 用于 URL 推导

## v3.1.2 (2026-07-25)

### 重构

1. **刮削逻辑完全重写，对齐绿联4800plus NAS影视中心识别格式**：
   - **tvshow.nfo**：plot/outline 用 CDATA 包裹（标准 XML 转义反转义后包裹），新增 lockdata/dateadded/sorttitle/rating/year/premiered/releasedate/runtime/country/mpaa/status 字段，移除 thumb 和 fanart 标签（图片文件直接放目录，绿联自动识别）
   - **season.nfo（新增）**：季信息 NFO，包含 plot/outline/lockdata/dateadded/title/year/sorttitle/premiered/releasedate/uniqueid/seasonnumber
   - **episode NFO**：plot 用 CDATA 包裹，outline 留空，新增 lockdata/dateadded/sorttitle/rating/year/runtime/season/episode/aired 字段，移除 thumb 标签（缩略图与视频同名 .jpg，绿联自动识别）
   - **movie.nfo**：与 tvshow 同样的字段结构，使用 movie 根标签

2. **目录结构对齐参考格式**：
   - 番剧目录：`番剧名 (年份)/`（自动从元数据获取年份并加到目录名）
   - Season 目录：`Season 01/`，内含 season.nfo 和复制自根目录的 poster.jpg
   - 单集文件命名：`番剧名 - S01E01 - 第 1 集.mp4` / `.nfo` / `.jpg`（与视频同名缩略图，绿联自动识别）

3. **图片生成完整覆盖绿联识别格式**：
   - 根目录生成：poster.jpg / backdrop.jpg / fanart.jpg / landscape.jpg / thumb.jpg / banner.jpg
   - backdrop 从 poster 裁剪 16:9 横版（如果 poster 是竖版），横版直接复制
   - fanart/landscape/thumb/banner 优先复制 backdrop，回退到 poster 裁剪
   - Season 目录复制 poster.jpg
   - 单集缩略图命名为 `番剧名 - S01E01 - 第 1 集.jpg`

4. **图片下载使用 cf_bypasser**：
   - `_download_cover_as_jpg` 改为通过 `cf_bypasser.direct_client` 下载（带正确 headers 和代理配置），避免裸 httpx 无法绕过 Cloudflare 防护导致 403 错误

5. **CDATA 处理**：
   - 新增 `_wrap_cdata` 静态方法，后处理 XML 将 plot/outline 标签内容用 `<![CDATA[...]]>` 包裹
   - 反转义 ET 自动转义的 XML 实体（&lt; / &gt; / &amp; 等），正确处理 CDATA 结束序列 `]]>`
   - 空标签（如 episode 的 `<outline/>`）保持不变

6. **其他改进**：
   - 新增常量：DEFAULT_RUNTIME_MINUTES=24、DEFAULT_COUNTRY="Japan"、SERIES_STATUS_CONTINUING="Continuing"、DEFAULT_RATING="7.6" 及所有图片文件名常量
   - `_find_existing_cover` 排除所有刮削生成的图片文件（backdrop/landscape/thumb/banner/fanart 等），避免误识别
   - `_reorganize_files` 新增 metadata_list 参数用于获取年份，目录重命名后同步更新 video_entries 中的文件路径
   - XML 声明 encoding 从 `UTF-8` 改为 `utf-8`（对齐参考格式）

## v3.1.1 (2026-07-25)

### 修复

1. **观看次数和上传日期解析失败（简体中文不兼容）**：
   - 源站部分页面使用简体中文"万"而非繁体"萬"，导致正则 `(\d+(?:\.\d+)?(?:萬|千)?)次` 匹配失败
   - 正则改为 `(?:萬|万|千)?` 同时兼容简繁体
   - `_parse_views` 方法同步加入简体"万"支持
   - 测试验证：video_id=406538 的观看次数 155.9万次 和日期 2026-06-05 现在能正确解析

2. **没有 cover 海报的视频无法下载封面**：
   - 部分视频（如 406538）在源站确实没有 `/image/cover/` 格式的竖版海报，只有 `/image/thumbnail/` 格式的横版预览图
   - 改为优先下载 cover 竖版海报，没有时回退到 thumbnail 横版预览图
   - 响应中新增 `is_poster` 字段标记是否为竖版海报，前端提示信息区分"竖版海报已保存"和"该视频没有竖版海报，已下载横版预览图"

## v3.1.0 (2026-07-25)

### 修复

1. **哈希ID封面海报无法获取的问题**：
   - **根因**：部分视频的 cover 图片文件名是哈希ID（如 `OmjQkYr`），不是数字 video_id（如 `39306`）。原代码用正则 `re.escape(video_id)` 匹配 cover URL 中的文件名，对哈希ID永远匹配不到，导致明明有海报却提示"无法获取海报"
   - **修复**：改用 BeautifulSoup 解析相关视频的详情页，查找指向当前视频的 `<a href="/watch?v={video_id}">` 链接，再获取链接内的 `/image/cover/` 格式 cover 图片。此方法不依赖 cover 文件名与 video_id 的关系，对数字ID和哈希ID均有效
   - **原理**：当前视频的详情页通常不会链接到自己，但在同系列/相关视频的详情页中，当前视频会作为相关视频出现并带有 cover 图片
   - 测试验证：video_id=39306 的封面已正确下载为 `OmjQkYr.jpg`（268x394 竖版海报），与用户手动验证的海报URL完全一致

## v3.0.9 (2026-07-25)

### 修复

1. **下载封面改为竖版海报，海报和预览图不再混用**：
   - 海报是海报（`/image/cover/` 格式，268x394 竖版），预览图是预览图（`/image/thumbnail/` 格式，横版），两者不再混用
   - 下载封面只下载 `/image/cover/` 格式的竖版海报
   - 获取不到海报格式时直接返回失败提示"该视频没有海报格式封面（cover），无法下载"，不再用预览图冒充海报
   - 前端只传 `video_id`，封面URL获取逻辑全部由后端处理

## v3.0.8 (2026-07-24)

### 修复

1. **下载封面按钮"未找到封面URL"错误**：
   - 前端 `searchVideos` 调用参数类型错误：传了 `(title, 1)` 两个参数，应为 `{ query: title, page: 1 }` 对象
   - 搜索未匹配到封面时增加回退：使用视频详情页的 poster URL 作为兜底

## v3.0.7 (2026-07-24)

### 修复

1. **下载封面改为首页海报**：
   - 之前下载的封面是视频详情页的 poster 截图（`h`后缀），不是首页列表展示的海报
   - 新增 `_get_cover_from_search()` 方法，通过搜索接口用视频标题搜索，匹配 video_id 获取首页海报URL（`l`后缀）
   - 在 `start_download` 和 `get_cover` API 中优先使用搜索获取的海报URL，搜索失败时回退到 poster
   - 测试验证：video_id=407017 的封面已正确下载为 `thumbnail/407017l.jpg`（首页海报）

## v3.0.6 (2026-07-24)

### 回退

1. **刮削逻辑回退至3.0.0版本**：
   - 删除 NFO 中的 `tmdbid` 字段（导致同系列合集识别失效）
   - 删除 NFO 中的 `landscape` 横版缩略图字段
   - 封面提取回退为仅使用 video poster
   - 后续将重新整理刮削逻辑，在下个版本中修复封面、合集识别等问题

## v3.0.5 (2026-07-24)

### 修复

1. **下载封面按钮导入错误**：
   - `POST /downloads/cover` 接口中 `from app.services.video_service import video_service` 报错，video_service.py 没有导出实例
   - scrape_service.py 中 `self.video_service.cf_bypasser` 同样的错误
   - 改为 `from app.utils.cloudflare_bypass import cf_bypasser`

2. **下载管理页面按钮改回grid布局**：
   - 手机端按钮从 flex 流式布局改回 grid 等宽排列
   - 768px以下左边4个按钮 `repeat(4, 1fr)`，右边2个 `repeat(2, 1fr)`
   - 480px以下全部 `repeat(2, 1fr)`

## v3.0.4 (2026-07-24)

### 新功能

1. **视频详情页下载封面按钮**：
   - 新增"下载封面"按钮，点击后下载封面到下载目录/covers/文件夹
   - 封面URL通过搜索接口获取（首页预览图），不是播放预览截图
   - 方便测试确认封面图是否正确

### 修复

1. **刮削封面下载失败（图片0个）**：
   - `_download_cover_as_jpg` 使用裸 httpx 下载无法绕过 Cloudflare 防护，导致所有封面下载403
   - 改为使用 `cf_bypasser.get_request()` 下载，正确绕过 Cloudflare

2. **下载管理页面手机端按钮不齐**：
   - 768px以下：移除 `justify-content: space-between`，改为 flex 流式布局统一间距
   - 480px以下：按钮每2个一行，字号缩小

## v3.0.3 (2026-07-24)

### 修复

1. **刮削封面图错误**：
   - 刮削时用的是视频播放预览截图而非番剧封面海报（和主页浏览到的不一样）
   - 详情页HTML中没有封面海报元素，改为通过搜索接口获取正确的封面URL
   - 新增 `_get_cover_from_search()` 方法，用标题搜索匹配 video_id 获取列表页封面

2. **同系列番剧未被识别为合集**：
   - tvshow.nfo 中新增 `<tmdbid>` 字段，使用系列标题哈希作为系列ID
   - 确保同系列不同集指向同一系列ID，绿联影视中心可正确识别合集

3. **视频详情页手机端按钮不齐**：
   - 768px以下：按钮从固定3列grid改为flex流式布局，每3个一行自动换行
   - 480px以下：每2个一行自动换行，按钮不再强制等宽导致不齐

## v3.0.2 (2026-07-24)

### 修复

1. **刮削封面模糊**：
   - 绿联影视中心列表页封面模糊
   - **根因1**：刮削时用的是 `<video>` 标签的 poster（播放预览截图），不是番剧封面海报。修改为先提取详情页中的 `main-thumb` 封面图，兜底才用 video poster
   - **根因2**：缺少横版缩略图。新增 landscape.jpg 生成，从竖版海报裁剪16:9中部横条，NFO中添加 `thumb aspect="landscape"` 声明
   - 封面下载时自动推断高分辨率URL（preview→poster、去除尺寸参数等），优先下载高分辨率版本
   - JPG输出质量提升至100（quality=100, subsampling=0），最高保真

## v3.0.1 (2026-07-24)

### 修复

1. **登录页选择框换行**：
   - "本地数据库"文字在小屏幕上换行
   - 添加 `white-space: nowrap` 防止换行

2. **登出后头像不消失**：
   - 登出后左上角头像和用户名需要刷新才消失
   - 登出时发出 `user-logout` 事件，AppSidebar 立即清除用户状态

3. **图片屏蔽设置不记忆**：
   - 本地登录模式下，换设备或重新登录后图片屏蔽设置总是变回默认毛玻璃
   - 移除模块级 `isInitialized` 锁定，改为监听登录/登出/storage事件自动刷新设置

4. **下载目录设置不记忆**：
   - 设置的下载目录重启/更新版本后变回默认
   - 新增 `save_download_dir_to_file()` 持久化函数，修改下载目录时自动保存到 `download_dir_settings.json`
   - 服务启动时自动从持久化文件恢复下载目录

## v3.0.0 (2026-07-24)

### 新功能

1. **里番自动刮削**：
   - 下载完成后自动生成NFO元数据文件，使绿联4800plus NAS影视中心能正确识别和显示影片信息
   - 支持电视剧模式（tvshow.nfo + Season目录结构）和电影模式（movie.nfo）
   - 自动生成Kodi/Emby/Jellyfin兼容的NFO XML文件，包含标题、简介、制作公司、标签、分级等信息
   - 成人内容自动标记NC-17分级

2. **封面图片JPG转换**：
   - 自动将封面转换为JPG格式（绿联影视中心仅识别JPG，PNG不被识别）
   - 使用Pillow库处理RGBA→RGB转换，白色背景填充透明通道
   - 自动生成poster.jpg（海报）和fanart.jpg（背景图）

3. **文件重命名与目录重组**：
   - 可选将视频文件重命名为S01E01标准格式（绿联影视中心识别需要）
   - 可选创建Season 01子目录结构（番剧名/Season 01/S01E01.mp4）
   - 按文件创建时间自动确定集号

4. **刮削API接口**：
   - GET /api/scrape/config — 获取刮削配置
   - PUT /api/scrape/config — 更新刮削配置
   - POST /api/scrape/series — 手动刮削指定番剧
   - POST /api/scrape/batch — 批量刮削所有番剧
   - GET /api/scrape/preview/{series_name} — 预览刮削效果
   - GET /api/scrape/scan — 扫描可刮削的番剧列表

5. **前端刮削界面**：
   - 设置页面新增"刮削"分区：刮削模式、自动刮削、文件重命名、目录重组、封面转换JPG开关
   - 下载页面新增"批量刮削"按钮和单个番剧"刮削"按钮
   - 重要提示：提醒用户在绿联NAS影视中心开启"优先本地信息"选项

### 配置项

- `SCRAPE_MODE`: 刮削模式，默认 `tv_show`（电视剧/电影）
- `AUTO_SCRAPE_AFTER_DOWNLOAD`: 下载完成后自动刮削，默认 `True`
- `SCRAPE_RENAME_FILE`: 重命名文件为S01E01格式，默认 `True`
- `SCRAPE_REORGANIZE_DIRECTORY`: 重组为Season目录结构，默认 `True`
- `SCRAPE_CONVERT_COVER_JPG`: 转换封面为JPG格式，默认 `True`

### 依赖

- 新增 `Pillow~=10.4.0`（图片格式转换）

## v2.5.1 (2026-07-17)

### 修复

1. **数据库表重建，严格遵循 LibraryDream 命名规范**：
   - 品牌共用表 `user` 更名为 `ld_user`，使用 `ld_` 品牌前缀
   - 所有关联表外键从 `user_id` 改为 `ld_user_id`，与引用表名一致
   - 索引名统一使用 `{prefix}_{table}_{columns}` 格式

2. **用户表字段专业化设计**：
   - 完整用户画像字段：`email`、`phone`、`nickname`、`real_name`、`avatar_url`
   - 新增 `gender`（TINYINT: 1=男/2=女/3=其他）、`birth_date`、`bio`
   - 用户类型 `user_type`（TINYINT, step 10: 10=普通/20=管理员/30=超级管理员）
   - 状态 `status`（TINYINT, step 10: 10=正常/20=禁用/30=封禁）
   - `is_active` 移除，由 `status` 字段统一管理
   - 新增 `last_login_at`、`last_login_ip` 登录追踪字段

3. **所有字段强制 COMMENT 注释**：状态/类型字段均列出完整枚举值

## v2.5.0 (2026-07-17)

### 新功能

1. **MySQL云数据库支持**：
   - 新增云数据库模式，用户数据可存储在远程 MySQL 服务器
   - 登录页面新增本地/云数据库切换按钮，用户可自由选择数据源
   - 共用用户表 `user` 设计，支持多个 LibraryDream 项目共用同一套用户账号
   - 项目特色数据（收藏、稍后观看、播放清单、观看历史、用户设置）通过关联表存储，以 `hanime_` 前缀区分

2. **数据库表结构设计**：
   - `user` — 多项目共用用户表（含软删除、激活状态）
   - `hanime_user_favorite` — 收藏关联表
   - `hanime_user_watch_later` — 稍后观看关联表
   - `hanime_user_playlist` / `hanime_user_playlist_video` — 播放清单（规范化设计，视频存储独立表）
   - `hanime_user_watch_history` — 观看历史关联表
   - `hanime_user_setting` — 用户设置（JSON字段）

3. **后端架构升级**：
   - 新增 `MySQLUserService` 服务类，基于 `aiomysql` 连接池
   - `UserService` 支持 SQLite/MySQL 双数据源路由
   - JWT Token 包含 `db_type` 和 `db_user_id` 字段
   - 所有用户数据 API（收藏、稍后观看、播放清单、观看历史、设置）均已适配双数据源
   - 登录认证、修改密码均支持本地和云数据库

4. **部署配置更新**：
   - `docker-compose.yml` 新增 MySQL 环境变量：`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`
   - `.env.example` 新增 MySQL 配置项
   - `requirements.txt` 新增 `aiomysql` 依赖

## v2.4.3 (2026-07-16)

### 优化改进

1. **全页面PC端布局大幅优化**：
   - 设置页 max-width 从 680px 提升至 900px
   - 收藏/稍后看/观看历史/下载页从 1000px 提升至 1200px
   - 播放清单从 1000px 提升至 1100px
   - 更新日志从 900px 提升至 1000px
   - 首页从 1200px 提升至 1400px
   - 搜索页新增 1200px 居中约束
   - 日历页从 1200px 提升至 1400px
   - 充分利用桌面宽屏空间，不再像手机端拉伸

2. **PC端页面标题全面增大**：
   - 设置页 32px、视频详情页 30px、收藏/稍后看/观看历史/下载/播放清单 28px
   - 搜索结果 24px、更新日志 36px、日历页 30px
   - 视觉层级更分明，PC端不再显得局促

3. **PC端卡片网格列宽和间距优化**：
   - 视频网格 minmax(200px, 1fr)，文件夹网格 minmax(260px, 1fr)
   - 下载番剧网格 minmax(260px, 1fr)
   - 间距统一增大至 18-20px，卡片之间呼吸感更强

4. **PC端内边距和留白增大**：
   - 各页面 padding 提升至 28-40px
   - 卡片区 padding 增大
   - 页面标题与内容间距增大

5. **PC端字体尺寸提升**：
   - 分区标题、表单标签、按钮文字、标签页等全部增大
   - 视觉层级更分明

6. **设置页数据管理按钮在PC端改为横排布局**

7. **搜索栏搜索输入框和按钮放大**：输入框 50px 高度、20px 字号，搜索/筛选按钮同步放大

8. **视频详情页操作按钮加大 padding，标签页字号增大，标签 tag 字号增大**

9. **日历页PC端视频网格改为6列**

10. **视频卡片PC端信息区 padding 增大，字号提升**

## v2.4.2 (2026-07-16)

### 优化改进

1. **视频分区PC端箭头导航**：
   - PC端横向滚动区域隐藏原生滚动条，改为左右箭头按钮导航
   - 左箭头仅在未滚动到最左侧时显示，右箭头仅在未滚动到最右侧时显示
   - 悬停箭头按钮持续缓慢滚动，点击箭头跳转一页宽度
   - 手机端保留原生触摸滚动，不显示箭头按钮
   - 箭头按钮为半透明圆形，毛玻璃效果，浅色主题适配

2. **视频详情页手机端按钮布局优化**：
   - 手机端操作按钮（下载/收藏/稍后看/播放列表）改为 grid 网格布局
   - 768px 以下 3 列网格，480px 以下 2 列网格，按钮等宽居中
   - PC端页面添加 max-width 1000px 居中布局，标题字号增大，网格列宽优化

3. **评论区分页功能**：
   - 评论列表新增分页控件（每页10条），替代原来的"加载更多"
   - 切换页码自动滚动到评论区顶部
   - 切换排序方式或加载新评论时自动重置到第一页

4. **播放清单页面图片屏蔽支持**：
   - 文件夹封面缩略图和文件夹内视频封面支持模糊/隐藏屏蔽
   - 集成 useContentSettings composable，根据用户设置自动应用屏蔽效果

5. **全页面PC端布局优化**：
   - 收藏/稍后看/观看历史/下载页面添加 max-width 1000px 居中约束
   - PC端专属样式优化，网格列宽和间距适配桌面显示

## v2.4.1 (2026-07-16)

### 优化改进

- **浅色模式 Banner 遮罩大幅减淡**：暗角从 `0.85→0.55`、品红从 `0.4→0.15`、晕影从 `0.25→0.12`、底部面板从 `0.5→0.3`，毛玻璃亮度提至 0.95，Banner 与浅色页面融为一体不再突兀

## v2.4.0 (2026-07-16)

### 新功能

1. **播放清单全面改版为文件夹式UI**：
   - 主页展示文件夹网格，每个文件夹显示前4个影片的封面缩略图
   - 点击文件夹进入内部视图，展示所有影片
   - 返回按钮 + 文件夹名称（可点击编辑）+ 删除按钮
   - 空文件夹显示大图标，空状态引导创建

2. **跨文件夹移动影片**：
   - 文件夹内影片卡 hover 显示"移动"和"移除"按钮
   - 点击"移动"弹出目标文件夹选择列表
   - 后端新增 `POST /api/accounts/me/playlists/move-video` 端点
   - `user_service` 新增 `move_video_between_playlists` 方法

3. **文件夹操作优化**：
   - 新建文件夹弹窗带图标前缀
   - 右键菜单：重命名 / 删除（危险色标注）
   - 文件夹名称可内联编辑
   - 删除时二次确认

### 优化改进

- 播放清单页面深浅主题全面适配（卡片 hover 发光、变量驱动颜色）
- 手机端 480px 以下 2 列网格布局，操作按钮常驻显示
- 页面居中 max-width 1000px 布局，视觉聚焦
- 标题加渐变色装饰条
- 文件夹数量指示 + 今天/昨天/月日 智能时间格式

## v2.3.5 (2026-07-16)

### 修复

1. **浅色模式 Banner 全面适配**：
   - 容器阴影减弱 + 空状态背景改为浅灰
   - "图片已隐藏"遮罩改为浅灰渐变 + 深色文字图标
   - 三层渐变遮罩（暗角/品红/晕影）透明度全面减弱
   - 底部信息面板渐变减弱
   - 指示器和导航箭头改为灰色半透明
   - 毛玻璃模式图片提亮（brightness 0.8 → 0.9）

2. **手机端侧边栏底部空缺修复**：
   - 打开菜单栏时锁定页面滚动（`html` + `body` 双保险 + `position: fixed`）
   - 兼容 iOS Safari 橡皮筋效果，保存并恢复滚动位置
   - 侧边栏容器增加 `100dvh` 动态视口高度

## v2.3.4 (2026-07-16)

### 修复

1. **切换深浅模式导致屏蔽图片设置重置**：
   - **根因**：后端 `save_user_settings` 使用 `INSERT OR REPLACE` 直接覆盖整个 settings 行。当 App.vue 切换主题调用 `saveThemeToServer` 只传 `{ theme: 'light' }` 时，之前保存的 `enableBlur` 和 `blurMode` 被清空
   - **修复**：`save_user_settings` 改为合并模式，先读取已有设置，用 `existing.update(settings)` 合并后再写入，只更新传入的字段

2. **浅色模式手机端 Header 未适配**：
   - `:global(.light)` 选择器在 scoped CSS 中有兼容性问题，改为 `html.light .app-header` 更可靠
   - 增加浅色边框 `border-bottom-color: #e5e7eb` 和微阴影

### 优化改进

1. **设置页面 UI 全面升级**：
   - 居中卡片式布局（max-width 680px）
   - 图标驱动分区标头（下载/代理/屏蔽/数据/安全/关于，各配专属图标）
   - 卡片 hover 边框发光 + 亮色模式阴影
   - 关于页从 `<p>` 段落改为 key-value 行式排版
   - 提示块增加细微边框 + 8px 圆角
   - 标题加渐变色装饰条（蓝→紫）

2. **侧边栏新增"更新记录"入口**：手机端隐藏顶部导航栏后，仍可通过侧边栏访问更新日志

3. **手机端设置页表单 label 防换行**：480px 以下 `el-form-item__label` 添加 `white-space: nowrap`

## v2.3.3 (2026-07-16)

### 优化改进

1. **下载进度实时更新**：
   - 修复下载页面进度条不自动更新的问题，无需手动点击刷新
   - `initializeDownloads` 不再阻塞重复调用，每次进入下载页都刷新最新数据
   - `refreshDownloads` 增加 WebSocket 自动重连逻辑
   - 新增5秒轮询兜底机制，确保 WebSocket 断开时也能获取进度更新

2. **手机端设置页适配**：
   - 修复"清空数据"确认对话框在手机上宽度过小导致文字溢出的问题
   - 弹窗宽度改为响应式（桌面480px / 移动90%）
   - 数据管理按钮在手机端改为纵向排列，避免文字截断

### 体验优化

1. **删除冗余成功提示**：
   - 移除全局 API 响应拦截器中的自动成功提示（此前每次请求都弹"操作成功"）
   - 移除下载开始/重新下载提示（下载开始 UI 已有反馈）
   - 移除刷新完成提示（刷新操作本身即为用户意图）
   - 移除暂停/恢复下载的重复提示（view层已提示，store层重复弹出）
   - 移除打开目录时的路径展示提示
   - 保留必要的用户操作提示：收藏/取消收藏、稍后观看、播放清单管理、设置保存、密码修改、数据清空/导入导出、头像更新等

## v2.3.2 (2026-07-16)

### 优化改进

1. **用户数据持久化**：
   - 新增 `DATA_ROOT` 配置项，所有用户数据（数据库、下载文件、封面等）统一存放到一个目录
   - Docker 部署只需挂载一个目录 `/app/backend/data` 即可持久化全部数据，更新镜像不再丢失收藏、稍后观看、观看历史、下载记录等
   - 支持通过 `DATA_ROOT` 环境变量自定义数据根目录
   - 旧部署配置中的 `DB_PATH`、`DOWNLOAD_PATH` 环境变量仍然有效，兼容旧配置

2. **代理设置持久化**：
   - 代理设置（USE_PROXY/PROXY_URL）通过设置页面修改后，现在会自动写入 `proxy_settings.json` 持久化文件
   - 服务重启后自动从文件恢复代理设置，不再丢失
   - 用户设置（图片屏蔽/模糊模式）存储在 `user.db` 的 `user_settings` 表中，同样在挂载范围内持久化

3. **自动数据迁移**：
   - 首次启动时自动检测旧路径（`/app/backend/db`、`/app/backend/downloads`），如有数据自动迁移到新路径（`/app/backend/data/db`、`/app/backend/data/downloads`），无需手动操作

3. **部署配置简化**：
   - `docker-compose.yml` 和 `docker-compose.nas.yml` 简化为只挂载一个目录
   - README 中的部署示例同步更新

## v2.3.1 (2026-07-16)

### 修复

1. **请求超时后全站不可用（根因修复）**：
   - **根本原因**：httpx `AsyncClient` 在请求超时后连接池被污染（损坏/半开连接），后续所有请求复用同一连接池导致全部失败
   - **修复方案**：在 `CloudflareBypasser` 的四个请求方法（`_direct_get_request`、`_direct_post_request`、`get_request`、`post_request`）中，所有重试耗尽抛出异常前，先调用 `_reset_direct_client()` / `_reset_client()` 关闭并清理客户端连接池，确保后续请求使用全新连接
   - **并发安全**：将 `client = await self.direct_client` 从方法级别移入重试循环内部，每次重试重新获取客户端引用，防止并发任务间互相干扰（一个任务重置了客户端，另一个任务使用已关闭引用导致 "client has been closed" 错误）

2. **lru_cache 缓存无效结果**：增强缓存过滤逻辑，新增 `_is_empty_result` 函数，检测并跳过空字符串、空列表、空字典、全空字段 Pydantic 模型的缓存

3. **头像选择弹窗手机端适配**：弹窗宽度在 480px 以下改为 90%，封面网格改为 2 列，缩小间距和字体

## v2.3.0 (2026-07-16)

### 优化改进

1. **首页 Banner 全面升级**：
   - 电影级多层渐变遮罩（暗角 + 品红渐变 + 底部聚焦）
   - Ken Burns 微缩放动画，画面缓慢推进
   - 发光播放按钮（品红渐变 + 阴影光晕）
   - 胶囊指示器替代圆点（激活时展开为胶囊形）
   - 高度增大至 420px，圆角增大至 16px
   - 导航箭头添加毛玻璃效果

2. **视频卡片精致化**：
   - 圆角增大 12px，添加微透明边框
   - 悬停时边框添加品红微光
   - 播放覆盖层改为底部渐变遮罩，更自然
   - 收藏按钮和徽章添加 backdrop-filter 毛玻璃
   - 标题行高增加，间距优化

3. **视频分区样式升级**：
   - 标题左侧竖条改为渐变发光效果
   - "查看更多"按钮改为胶囊圆角 + 渐变背景
   - 滚动条优化为品红半透明
   - 分隔线改为微透明

4. **顶部导航栏毛玻璃效果**：sticky 导航栏添加 backdrop-filter 模糊，滚动时更有层次感

## v2.2.0 (2026-07-16)

### 新增功能

1. **扫描恢复下载记录**：重新部署后，点击"扫描恢复"按钮可自动从下载目录恢复丢失的下载记录，从文件名解析 video_id 并补建数据库记录

2. **番剧分组视图**：下载中心新增"番剧"视图模式，按番剧系列分组展示下载内容，显示番剧封面、集数、总大小和完成进度

3. **番剧详情弹窗**：点击番剧卡片展开所有集的列表，可直接播放已完成的视频

4. **下载搜索**：下载中心顶部新增搜索框，支持按番剧名/文件名搜索（列表和番剧模式均可用）

5. **清除已完成/失败记录**：一键清除已完成或失败的下载记录（不删除文件）

### 优化改进

1. **下载中心 UI 重构**：顶部搜索栏 + 视图切换（列表/番剧），操作按钮分为左右两行更清晰

2. **下载历史 API 支持搜索和过滤**：`/downloads/history` 接口新增 `search` 和 `status` 查询参数

3. **手机端适配**：番剧卡片网格在 480px 以下自动变为 2 列，操作按钮允许换行

## v2.1.5 (2026-07-16)

### 优化改进

1. **全局防横向溢出**：添加 `html, body { overflow-x: hidden }` 基础规则，彻底消除手机端横向滚动条

2. **AppHeader 手机端适配**：480px 以下隐藏"更新日志"图标按钮，缩小间距和字体；360px 以下隐藏"日历"按钮，防止右侧溢出

3. **VideoDetailPage 手机端适配**：视频操作按钮区域添加 `flex-wrap: wrap` 允许换行，480px 以下缩小按钮尺寸和标签尺寸

4. **VideoSection 手机端适配**：480px 以下横向滚动项目宽度改为百分比（45%/32%），缩小间距和字体

5. **SearchPage 手机端适配**：搜索栏添加内边距防止贴边，480px 以下缩小搜索框和按钮尺寸，活跃过滤器标签允许换行

6. **Settings 手机端适配**：768px 以下缩小表单 label 宽度，480px 以下进一步缩小并允许按钮换行

## v2.1.4 (2026-07-16)

### 修复

1. **满屏请求错误/超时提示**：修复搜索时可能触发大量请求错误提示导致满屏的问题，添加错误消息节流机制（相同错误3秒内只显示一次）

2. **网站无法获取视频（缓存空结果/404）**：修复后端 `lru_cache` 缓存失败结果导致后续所有请求持续返回错误的问题。根本原因：`get_video_detail` 等方法失败时返回空对象，被 API 端点判断为"不存在"返回 404，404 响应被缓存1小时，导致整个网站无法使用。修复后：失败时抛出异常（不被缓存），API 返回 503（服务暂时不可用），下次请求会重新尝试

3. **401重复跳转**：修复 token 过期时多个请求同时触发 `window.location.href` 导致重复跳转的问题

4. **搜索加载更多失败跳页**：修复 `loadMore` 请求失败后页码不回退导致跳页的问题

5. **API端点函数名冲突**：修复 `search_combination` 和 `search` 两个端点的处理函数同名 `search_videos` 的问题

### 优化改进

1. **前端请求超时设置**：axios 实例添加 30 秒超时，避免请求积压导致后端工作线程被占满

2. **后端请求超时优化**：`cloudflare_bypass` 的 httpx 客户端超时从 60 秒减少到 30 秒，加快失败检测

3. **后端异常处理优化**：`video_service` 所有方法（`search_videos`、`get_search_combination`、`get_home_data`、`get_video_detail`、`get_video_comments`、`get_comment_replies`、`get_calendar_data`）在失败时抛出异常而非返回空对象，确保错误结果不会被 lru_cache 缓存

4. **503 静默处理**：前端对 503（服务暂时不可用）错误不弹提示，由各页面组件自行处理降级显示

5. **全局异常响应码**：后端全局异常处理器从 500 改为 503，区分"服务器内部错误"和"外部服务暂时不可用"

## v2.1.3 (2026-07-15)

### 新增功能

1. **修改密码功能**：设置页面新增"账号安全"卡片，支持修改用户密码（需验证旧密码，新密码最少6位）

2. **稍后观看优化**：观看视频后自动从稍后观看列表移除（播放5秒后自动移除），稍后观看页面新增"开始观看"按钮

### 优化改进

1. **区分收藏与稍后观看**：收藏为永久标记（个人影片库），稍后观看为临时待看队列（观看后自动移除）

2. **用户密码持久化**：用户密码从硬编码改为数据库存储（PBKDF2-SHA256 哈希），Docker 重新部署不再丢失用户数据

### 修复

1. **观看历史未生效**：修复进入视频详情页未记录观看历史的问题，现在访问视频自动记录

2. **Docker 重新部署数据丢失**：用户凭证存储在数据库中（挂载卷内），重建容器不再丢失用户数据

## v2.1.2 (2026-07-15)

### 修复

1. **内容屏蔽设置浏览器刷新后恢复默认**：修复 `useContentSettings` composable 初始化逻辑，确保从服务端加载设置后正确应用，不再重置为默认值

2. **收藏/稍后观看/播放清单 API 422 错误**：修复前端 API 调用参数传递方式，将 `params` 从 request body 改为 URL 查询参数，匹配后端 `Query()` 接收方式

3. **收藏/稍后观看等 API 500 错误**：修复旧数据库表缺少 `username` 列导致所有用户数据操作失败的问题，添加数据库迁移逻辑自动为旧表添加 `username` 列并迁移数据

4. **下载封面和用户头像不显示毛玻璃屏蔽**：修复 DownloadItem 中 `blurMode` 变量名不匹配问题，为 AppSidebar 用户头像添加毛玻璃/隐藏屏蔽效果

5. **下载列表不实时更新**：修复添加下载后需要手动刷新页面才能看到下载项的问题

## v2.1.1 (2026-07-15)

### 修复

1. **封面图片无法显示**：修复下载页面和头像选择中封面图片无法加载的问题（`<img>` 标签无法发送 Authorization header，改为通过 URL 查询参数传递 token）

2. **用户头像选择后无法显示**：头像 URL 添加 token 认证参数

3. **下载列表不实时更新**：添加下载后自动刷新下载列表，无需手动刷新浏览器

4. **登录后侧边栏仍显示"未登录"**：修复 computed 不响应 localStorage 变化的问题（v2.1.0 遗留问题）

5. **内容屏蔽设置不持久化**：修复浏览器刷新后内容屏蔽设置恢复默认的问题（已通过用户设置 API 持久化）

### 优化改进

1. **主题模式绑定用户**：明亮/暗黑模式切换后保存至服务端，跨设备/浏览器保持一致

2. **代理设置提示**：添加 Docker 环境下使用 `host.docker.internal` 代替 `127.0.0.1` 的提示

## v2.1.0 (2026-07-15)

### 新增功能

1. **Banner 轮播图**
   - 首页 Banner 改为自动轮播，每 5 秒切换
   - 左右导航箭头，鼠标悬停时显示
   - 底部圆点指示器，点击跳转
   - 鼠标悬停时暂停轮播
   - 从推荐视频中自动提取多个 Banner

2. **收藏功能**
   - 视频卡片添加快速收藏按钮，悬停时显示爱心图标
   - 视频详情页添加收藏、稍后观看、加入播放清单按钮
   - 收藏状态实时同步（卡片和详情页）

3. **用户收藏夹实装**
   - 喜欢的影片：收藏视频列表，支持移除和清空
   - 稍后观看：稍后观看列表，支持移除和清空
   - 播放清单：创建/删除/重命名清单，添加/移除视频
   - 观看历史：自动记录观看进度，支持清空和删除

4. **播放清单对话框**
   - 视频详情页可直接添加到已有播放清单
   - 支持内联创建新播放清单

### 优化改进

1. **新番列表页面重设计**
   - 全新高级 UI 设计，Tab 过滤器按类型筛选
   - 视频卡片网格布局（5/4/3/2 列响应式）
   - 分类标题彩色竖条和计数徽章
   - 平滑展开/收起动画
   - 毛玻璃内容屏蔽支持

2. **登录状态修复**：修复登录后侧边栏仍显示"未登录"的问题

3. **毛玻璃模式优化**：移除遮挡图标和"已屏蔽"文字，只保留模糊效果

4. **明亮模式优化**
   - 修复中间区域背景黑色问题
   - 替换所有硬编码暗色背景为 CSS 变量
   - 添加 Element Plus 亮色模式全局变量覆盖
   - 优化卡片、输入框、对话框、骨架屏、滚动条等组件

5. **搜索结果标题提取优化**：修复"最新上市"和"他们在看"查看更多只显示缩略图无标题的问题

### 修复

1. 修复侧边栏用户名 computed 非响应式导致登录后显示"未登录"
2. 修复多个组件 blur-overlay 包含冗余文字和图标
3. 修复亮色模式下多个页面背景仍为黑色

## v2.0.1 (2026-07-15)

### 新增功能

1. **用户登出按钮**：侧边栏左上角添加登出按钮，确认后清除登录状态并跳转到登录页

2. **用户头像功能**
   - 默认显示用户名首字母作为头像
   - 点击头像可从已下载番剧封面中选择自定义头像
   - 头像自适应圆形头像框
   - 支持恢复默认头像
   - 不允许用户自行上传头像

3. **头像持久化**：头像选择与用户绑定，切换账号后自动加载对应头像

### 优化改进

1. **记住账号密码**：登录页添加记住账号和记住密码功能，勾选后本地存储

2. **侧边栏用户区域优化**：显示当前登录用户名，不再硬编码显示"未登录"和"H1"

3. **移除登录页默认凭据**：登录页不再显示默认账号密码，仅保留在 README 中

4. **版本号更新**：v2.0.0 → v2.0.1

### 修复

1. **修复刷新 500 错误**：添加数据库迁移逻辑，修复旧表缺少 `username` 列导致 `/api/downloads/history` 报 500

2. **修复登录页报错**：首次进入登录页不再请求 `/api/downloads/history`，避免"Not authenticated"错误

## v2.0.0 (2026-07-15)

### 新增功能

1. **用户登录系统**
   - 添加 JWT 认证机制，所有 API 请求需要登录后才能访问
   - 创建精美的登录页面，支持毛玻璃效果和动画
   - 默认用户名：`admin`，默认密码：`666666`（暂不开放注册）
   - Token 有效期为 24 小时
   - 未登录访问任何路由会自动跳转至登录页
   - 后端所有 API 端点添加登录验证依赖

2. **敏感图片屏蔽**
   - 在设置页面添加内容屏蔽设置区域
   - 支持两种屏蔽方式：毛玻璃打码和不显示图片
   - 默认启用毛玻璃打码模式
   - 覆盖所有视频封面、播放器封面、横幅、下载列表等位置

3. **用户数据隔离**
   - 收藏、稍后观看、播放清单、观看历史和下载记录均与用户绑定
   - 切换账号后自动加载对应用户的数据
   - 用户设置（内容屏蔽等）持久化存储并与用户关联
   - 每个用户拥有独立的默认设置值

4. **下载目录设置**：设置页新增下载目录选择功能，支持绝对路径输入（兼容 Windows/Linux/Docker 环境）

5. **打开目录按钮**：设置页新增"打开目录"按钮，本地环境可直接打开文件管理器，Docker 环境显示路径信息

6. **首页刷新按钮**：首页右上角新增刷新按钮，点击后清除后端缓存并重新获取推荐内容

7. **Logo 刷新推荐**：点击首页 Logo 时，若已在首页则触发刷新推荐内容

8. **新番列表页**：全新日历/新番列表页面，按类型（里番、泡面番、Motion Anime、3DCG 等）展示最新番剧

9. **事件总线**：新增 mitt 事件总线工具，实现跨组件通信

10. **骨架屏**：首页、日历页、轮播图等组件加载时显示骨架屏占位

11. **界面动画增强**
    - 添加全局动画样式文件，包含淡入、滑入、缩放等多种动画
    - 路由切换动画（左右滑动 + 淡入淡出）
    - 侧边栏滑入动画和导航项悬停效果
    - 视频卡片悬停动画（上浮、缩放、阴影加深）
    - 视频卡片交错入场动画

12. **版本号显示**：在头部和设置页面显示当前版本号

### 优化改进

1. **视频标题提取优化**
   - 修复搜索和查看更多页面只有预览图没有标题的问题
   - 增加多种标题选择器和图片alt属性作为备选
   - 优化标题提取逻辑，支持更多页面结构

2. **代理地址自动补全**：在设置页面输入代理地址时自动补全 `http://` 前缀

3. **下载目录结构**：封面直接保存在番剧子目录中（`{video_id}.jpg`），不再单独创建 `covers/` 子目录

4. **封面查找逻辑**：封面查找优先遍历番剧子目录，回退到全局封面目录，最后实时下载

5. **下载目录路径校验**：
   - 新增 `_is_absolute_path` 函数，兼容 Windows（`C:\`）和 Linux（`/`）绝对路径
   - Linux/Docker 环境下输入 Windows 路径时给出明确提示
   - 自动去除路径末尾的斜杠

6. **Docker 挂载提示**：设置页新增 Docker 环境卷挂载说明，docker-compose.yml 添加注释示例

### 修复

- **搜索结果解析**：修复搜索视频返回0个结果的问题，新增搜索结果页 HTML 结构解析（`_extract_search_result_video`），兼容多种页面结构
- **查看更多链接**：修复"最新里番"和"泡面番"的"查看更多"点击后无结果的问题
  - search_suffix 保留繁体原文，不再转为简体
  - 为"最新"类分区自动补充 `sort=最新上市` 参数
- **日历数据获取**：修复日历页面无法解析数据的问题，改用搜索 API 按类型构建新番列表
- **DB_PATH 环境变量**：修复 config.py 中 DB_PATH 错误引用 DOWNLOAD_PATH 环境变量的问题

## v1.1.0 (2026-07-15)

### 主要更新

1. **大幅优化内存占用**
   - 从 >1GB 降至约 65MB

2. **移除 DrissionPage + Chromium 依赖**
   - 改用 BeautifulSoup + lxml

3. **移除 CF Bypass 服务依赖**
   - 简化部署配置

4. **使用 zhconv 替代 opencc**
   - 解决 Alpine 兼容性问题

## v1.0.1 (2026-07-14)

### 修复与优化

1. 修复视频详情页 upload_date 验证错误
2. 修复视频流 URL 为空导致无法播放和下载的问题
3. 添加从 JavaScript 中提取视频流 URL 的支持
4. 修复 GitHub Actions 镜像标签大小写问题

## v1.0.0 (2026-07-13)

### 初始版本

1. 添加用户收藏系统（喜欢的影片）
2. 添加稍后观看列表功能
3. 添加播放清单功能
4. 添加观看历史记录
5. 添加设置页面（代理配置、数据管理）
6. 添加 GitHub Actions 自动构建多平台镜像
7. 创建 NAS 专用 docker-compose.nas.yml
8. 修复页面 404 问题
9. 修复 Cloudflare 绕过问题
10. 修复页面内容解析问题

## 修改原因

1. **原项目兼容性问题**: 原项目使用 DrissionPage 依赖 Chromium，在 Alpine Docker 环境下无法正常运行
2. **内存占用过高**: DrissionPage + Chromium 组合导致内存占用超过 1GB，不适合 NAS 部署
3. **代理配置不便**: 需要运行时可切换代理设置
4. **缺少用户功能**: 没有收藏、观看历史等用户功能
5. **安全性需求**: 需要登录验证保护敏感内容
