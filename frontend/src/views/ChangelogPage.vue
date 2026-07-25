<template>
  <div class="changelog-page">
    <div class="page-header animate-fade-in-down">
      <h1 class="page-title">更新日志</h1>
      <p class="page-subtitle">记录项目的所有版本更新</p>
    </div>

    <div class="changelog-container">
      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.5</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复刮削时 video_id 提取失败导致 NFO 内容缺失：</strong>重命名后的文件名无法提取 video_id，导致重新刮削时 NFO 内容全部丢失。现在新增从同名 NFO 文件和数据库下载记录中回退查找 video_id，确保元数据能正确获取</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复文件名和 NFO 标题包含年份后缀：</strong>目录名"番剧名 (2017)"中的年份不应出现在文件名和 NFO 标题中，现在统一去除年份后缀，年份仅保留在目录名中</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复刮削重命名时残留旧附属文件：</strong>视频文件重命名时，同名的旧 NFO/JPG 文件现在会自动清理，避免 Season 目录中残留错误的元数据文件</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.3</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载时自动检测同系列番剧并合并目录：</strong>下载时自动从源站读取系列信息，如果检测到同系列视频已下载，自动将新视频放入同一目录的对应 Season 子目录，第一部自动整理到 Season 1，目录名自动重命名为系列基础名（去掉编号后缀）</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.2</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>系列合并功能：</strong>视频详情页系列影片区域新增"合并到系列"按钮，当当前视频和至少一个系列视频都已下载时显示，支持编辑系列名称和调整季号；下载管理页面新增"合并系列"按钮，可选择多个已下载番剧合并到同一系列；系列名自动从标题中提取（如"不潔之星・赤"→"不潔之星"）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削多季支持：</strong>合并后的系列刮削时自动识别 Season 1/Season 2 等目录，每季独立编号集号，为每季生成 season.nfo 和 season-poster.jpg，重命名文件使用正确的 S02E01 格式</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.1</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复删除下载记录时无法删除刮削后重命名的文件：</strong>刮削服务会将视频从原始命名重命名为 S01E01 标准格式，旧删除逻辑只查找原始路径导致文件残留。现在通过 NFO 中的 uniqueid 标签递归搜索番剧目录，精确定位刮削后的视频文件、NFO、缩略图和封面并一并删除</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>扫描恢复增加清理无效记录：</strong>检查所有已完成的下载记录，如果文件在原始路径和刮削后路径都不存在，自动清理数据库记录，避免"幽灵"下载项</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>菜单"喜欢的影片"更名为"收藏的番剧"：</strong>侧边栏菜单和收藏页面标题统一更名为"收藏的番剧"</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.0</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复视频详情页日期解析失败的问题：</strong>源站页面结构中"观看次数+日期"不在第一个子div中，旧代码只取第一个div导致正则匹配失败。现在遍历所有子div查找包含"次+日期"格式的元素，确保无论页面结构如何变化都能正确解析上传日期和观看次数</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复副标题被错误解析为"观看次数"的问题：</strong>之前 subtitle 会显示为"观看次数：363.2万次 2017-09-28"，现在正确识别为番剧副标题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.9</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>彻底修复绿联显示 1970 年问题：</strong>NFO 写入时自动移除空日期标签；新增"修复NFO"按钮可一键扫描修复所有已有 NFO 文件中的空标签</span>
            </li>
          </ul>
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复NFO工具：</strong>下载管理页面新增"修复NFO"按钮，一键扫描并移除 NFO 中的空日期标签，解决绿联影视中心显示 1970-01-01 的问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.8</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复绿联影视中心显示 1970 年的问题：</strong>NFO 文件中当日期字段（year/premiered/releasedate/aired）值为空时，不再创建空标签（如 &lt;premiered/&gt;），避免绿联将空值解析为 1970-01-01。涉及 tvshow.nfo、episode.nfo、movie.nfo 共 6 处</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.7</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>预览图从视频真实画面截取：</strong>刮削时 backdrop.jpg / landscape.jpg / 单集缩略图优先从已下载的视频文件用 ffmpeg 截取真实画面，不再使用源站预览图。backdrop 取视频 50% 位置，landscape 取 70% 位置，确保画面不重复</span>
            </li>
          </ul>
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>Docker 镜像集成 ffmpeg：</strong>基础镜像新增 ffmpeg 安装，支持视频截帧功能</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.6</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复 download.ts 类型推断错误：</strong>将速度平滑处理器（DownloadSpeedSmoother 单例）从 Pinia 响应式 state 移至模块级变量，解决类实例放入 state 导致 TypeScript 无法推断出 downloads 等属性的问题</span>
            </li>
          </ul>
          <h3 class="section-title">清理</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>删除根目录无用测试文件：</strong>移除 test_cover.py ~ test_cover5.py 共5个封面下载调试脚本</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.5</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载管理批量删除功能：</strong>新增"批量删除"按钮，进入批量模式后可勾选多条记录，支持全选/取消选择，确认删除时可选是否删除源文件</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>删除时可选是否删除源文件：</strong>删除源文件将删除视频+刮削NFO+图片；仅删记录则保留所有文件。智能清理：番剧目录无视频后自动删除整个目录</span>
            </li>
          </ul>
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>视频详情页手机端按钮对齐优化：</strong>修复480px断点下按钮宽度不一致、高度不齐、内容不居中等问题，设置固定高度并统一图标文字间距</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载管理手机端按钮布局优化：</strong>768px断点下改为3列网格适配新增按钮，批量操作栏手机端自动切换为垂直布局</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.4</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>NFO 字段顺序完全对齐绿联4800plus 参考格式：</strong>参考"Y:\links\电视剧\日番\未来日记 (2011)"，tvshow/episode/movie NFO 字段顺序重新排列，episode NFO 中 episode 字段移到 season 之前</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>新增关键字段：</strong>tvshow.nfo 新增 enddate（最新集日期）、episodeguide、id、season(-1)、episode(-1)、displayorder(aired)；episode.nfo 新增 uniqueid；movie.nfo 新增 id</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>runtime 时长准确解析：</strong>新增 _parse_duration_to_minutes 方法，从源站 duration 字符串（如 "23:45"）解析为分钟数（向上取整到 24），支持 HH:MM:SS/MM:SS/带单位数字/纯数字四种格式，不再固定 24 分钟</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>新增 season01-poster.jpg：</strong>参考格式根目录包含此文件，自动从 poster.jpg 复制生成，绿联NAS通过此文件识别第1季海报</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>mpaa 分级调整：</strong>从 NC-17 改为 TV-MA（对齐参考格式"未来日记"），TV-MA 是电视节目分级，更适合番剧类型</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>_find_existing_cover 排除规则增强：</strong>新增正则排除 season\d+-poster 模式，避免误将 season01-poster.jpg 识别为已有封面导致跳过下载</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.3</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>Season 目录命名对齐参考格式：</strong>Season 01 → Season 1（不带前导零），文件名中的 S01E01 格式保持不变</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>图片质量全面提升：</strong>新增 _get_horizontal_thumbnail_url 方法从 cover URL 推导横版缩略图 URL，backdrop/fanart/landscape/thumb 改用 thumbnail URL 下载原生横版 1024x576 图片，poster 放大到 1000x1426，backdrop 放大到 1920x1080，banner 长宽比修正为 5.4:1（1000x185）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>新增图片处理方法：</strong>_crop_banner_from_landscape（5.4:1 裁剪）、_upscale_to_standard（仅放大）、_resize_to_standard（裁剪+缩放），均使用 PIL LANCZOS 重采样</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>日期处理更健壮：</strong>同时兼容 date 和 datetime 对象（video_service 返回的是 date 对象），所有 NFO 中的 year/premiered/releasedate/aired 字段处理统一</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.1.2</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">重构</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削逻辑完全重写，对齐绿联4800plus NAS影视中心识别格式：</strong>tvshow.nfo/season.nfo/episode NFO/movie.nfo 全部按参考格式生成，plot/outline 用 CDATA 包裹，新增 lockdata/dateadded/sorttitle/rating/year/premiered/releasedate/runtime/country/mpaa/status 等字段，移除 thumb 和 fanart 标签（图片文件直接放目录，绿联自动识别）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>目录结构对齐参考格式：</strong>番剧目录自动加年份（番剧名 (年份)/），Season 01 目录内含 season.nfo 和复制自根目录的 poster.jpg，单集文件统一命名为"番剧名 - S01E01 - 第 1 集.mp4/.nfo/.jpg"</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>图片生成完整覆盖绿联识别格式：</strong>根目录生成 poster/backdrop/fanart/landscape/thumb/banner 六种图片，backdrop 从 poster 裁剪 16:9 横版，其他优先复制 backdrop；单集缩略图与视频同名 .jpg，绿联自动识别</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>图片下载使用 cf_bypasser：</strong>改用 cf_bypasser.direct_client 下载（带正确 headers 和代理配置），避免裸 httpx 无法绕过 Cloudflare 防护导致 403 错误</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>CDATA 处理：</strong>新增 _wrap_cdata 静态方法，后处理 XML 将 plot/outline 标签内容用 CDATA 包裹，反转义 ET 自动转义的 XML 实体，空标签保持不变</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.1.1</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>观看次数和上传日期解析失败：</strong>源站部分页面使用简体中文"万"而非繁体"萬"，导致正则匹配失败。改为同时兼容简繁体，video_id=406538 的 155.9万次和 2026-06-05 现在能正确解析</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>没有 cover 海报的视频无法下载封面：</strong>部分视频在源站确实没有 /image/cover/ 格式竖版海报。改为优先下载竖版海报，没有时回退到 thumbnail 横版预览图，提示信息中明确区分</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.1.0</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>哈希ID封面海报无法获取的问题：</strong>部分视频的 cover 文件名是哈希ID（如 OmjQkYr）而非数字 video_id（如 39306），原正则匹配永远找不到。改为从相关视频详情页用 BeautifulSoup 查找指向当前视频的链接及其 cover 图片，对数字ID和哈希ID均有效</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.9</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载封面改为竖版海报：</strong>海报和预览图不再混用。下载封面只下载 /image/cover/ 格式的竖版海报（268x394），获取不到海报时直接返回失败提示，不再用 /image/thumbnail/ 格式的横版预览图冒充海报</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.8</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载封面按钮"未找到封面URL"错误：</strong>前端搜索接口调用参数类型错误导致始终搜索失败，已修正；搜索未匹配时回退到视频poster</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.0.7</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载封面改为首页海报：</strong>之前下载的是视频详情页poster截图（h后缀），现新增搜索匹配方法获取首页列表海报URL（l后缀），搜索失败时回退到poster</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="warning" size="large">v3.0.6</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">回退</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>刮削逻辑回退至3.0.0版本：</strong>删除NFO中tmdbid和landscape字段，封面提取回退为video poster，后续重新整理逻辑再修复</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.5</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载封面按钮导入错误：</strong>video_service模块无实例导出，改为直接导入cf_bypasser</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载管理页面按钮改回grid布局：</strong>等宽排列更整齐，768px四列/480px两列</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.4</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><SuccessFilled /></el-icon>
              <span><strong>视频详情页下载封面按钮：</strong>点击后下载封面到covers目录，封面URL通过搜索接口获取（首页预览图）</span>
            </li>
          </ul>
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>刮削封面下载失败：</strong>使用裸httpx无法绕过Cloudflare导致封面下载失败，改为使用cf_bypasser正确下载</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载管理页面手机端按钮不齐：</strong>改为flex流式布局，统一间距和排列</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.3</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>刮削封面图错误：</strong>用的是播放预览截图而非番剧封面海报，改为通过搜索接口获取正确封面URL</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>同系列番剧未识别为合集：</strong>tvshow.nfo新增tmdbid系列标识，绿联影视中心可正确识别合集</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>视频详情页手机端按钮不齐：</strong>改为flex流式布局，自动换行不再不齐</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.2</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>刮削封面模糊：</strong>根因1-封面用了播放预览图而非番剧海报（已修复提取逻辑）；根因2-缺少横版缩略图（已添加landscape.jpg）；高分辨率URL推断+JPG最高质量输出</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v3.0.1</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>登录页选择框换行：</strong>"本地数据库"文字在小屏幕上换行，添加nowrap防止换行</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>登出后头像不消失：</strong>登出后左上角头像需刷新才消失，登出时立即清除用户状态</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>图片屏蔽设置不记忆：</strong>本地登录模式下设置总是变回默认毛玻璃，改为监听登录/登出事件自动刷新设置</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span><strong>下载目录设置不记忆：</strong>重启/更新版本后下载目录变回默认，新增持久化保存和自动恢复</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="primary" size="large">v3.0.0</el-tag>
          <span class="version-date">2026-07-24</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>里番自动刮削：</strong>下载完成后自动生成NFO元数据文件，使绿联4800plus NAS影视中心能正确识别和显示影片信息，支持电视剧模式（tvshow.nfo）和电影模式（movie.nfo）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>封面图片JPG转换：</strong>自动将封面转换为JPG格式（绿联影视中心仅识别JPG），生成poster.jpg和fanart.jpg</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>文件重命名与目录重组：</strong>可选将视频文件重命名为S01E01标准格式，创建Season 01子目录结构</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削API接口：</strong>提供config/series/batch/preview/scan等完整API，支持手动和批量刮削</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>前端刮削界面：</strong>设置页面新增刮削分区，下载页面新增批量刮削和单个刮削按钮</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag size="large" type="warning">v2.5.1</el-tag>
          <span class="version-date">2026-07-17</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>数据库表重建：</strong>品牌共用表更名为 ld_user，外键统一改为 ld_user_id，严格遵循 LibraryDream 命名规范</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>用户表字段专业化：</strong>新增 email、phone、nickname、real_name、avatar_url、gender、birth_date、bio 等完整用户画像字段</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>枚举规范化：</strong>user_type（10=普通/20=管理员/30=超级管理员）、status（10=正常/20=禁用/30=封禁），step 10 递进</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>登录追踪：</strong>新增 last_login_at（最后登录时间）和 last_login_ip（最后登录IP）字段</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>全字段 COMMENT：</strong>所有表和字段均有注释，状态/类型字段列出完整枚举值</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag size="large" type="danger">v2.5.0</el-tag>
          <span class="version-date">2026-07-17</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>MySQL云数据库支持：</strong>用户数据可存储在远程 MySQL 服务器，登录页面新增本地/云数据库切换按钮，用户可自由选择数据源</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>多项目共用用户表：</strong>设计共用 user 表，支持多个 LibraryDream 项目共用同一套用户账号和密码</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>项目特色数据关联表：</strong>收藏、稍后观看、播放清单、观看历史、用户设置通过 hanime_ 前缀的关联表存储，与共用用户表解耦</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>播放清单表规范化：</strong>MySQL模式下播放清单拆分为 hanime_user_playlist 和 hanime_user_playlist_video 两张表，视频不再存为JSON</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>双数据源架构：</strong>UserService 支持 SQLite/MySQL 双数据源自动路由，JWT Token 包含 db_type 字段区分数据来源</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>全API适配：</strong>收藏、稍后观看、播放清单、观看历史、用户设置、认证、修改密码等所有用户相关API均已适配双数据源</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>部署配置：</strong>Docker Compose 新增 MySQL 环境变量配置，.env.example 新增云数据库配置项，requirements.txt 新增 aiomysql 依赖</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag size="large">v2.4.3</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>全页面PC端布局大幅优化：设置页 max-width 提升至 900px，收藏/稍后看/观看历史/下载页提升至 1200px，播放清单提升至 1100px，更新日志提升至 1000px，首页提升至 1400px，搜索页和日历页提升至 1200px/1400px，充分利用桌面宽屏空间</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>PC端页面标题全面增大：设置页 32px、视频详情页 30px、收藏/稍后看/观看历史/下载/播放清单 28px、搜索结果 24px、更新日志 36px、日历页 30px</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>PC端卡片网格列宽和间距优化：视频网格 minmax(200px, 1fr)、文件夹网格 minmax(260px, 1fr)、番剧网格 minmax(260px, 1fr)，间距统一增大至 18-20px</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>PC端内边距和留白增大：各页面 padding 提升至 28-40px，卡片区 padding 增大，页面标题与内容间距增大</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>PC端字体尺寸提升：分区标题、表单标签、按钮文字、标签页等全部增大，视觉层级更分明</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>设置页数据管理按钮在PC端改为横排布局，搜索栏搜索输入框和按钮放大</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>视频详情页操作按钮加大 padding，标签页字号增大，标签 tag 字号增大</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>日历页PC端视频网格改为6列，搜索页结果网格加宽，视频卡片PC端信息区 padding 增大</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag size="large">v2.4.2</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>视频分区PC端箭头导航：隐藏原生滚动条，改为左右箭头按钮，悬停持续滚动，点击跳转一页，手机端保留触摸滚动</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>视频详情页手机端按钮改为 grid 网格布局，768px以下3列、480px以下2列，按钮等宽居中</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>视频详情页PC端优化：max-width 1000px 居中布局，标题字号增大，网格列宽优化</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>评论区分页功能：每页10条评论，替代"加载更多"，切页自动滚动到顶部</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>播放清单页面图片屏蔽支持：文件夹封面和视频封面支持模糊/隐藏屏蔽</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>全页面PC端布局优化：收藏/稍后看/观看历史/下载页面添加居中约束和PC端专属样式</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag size="large">v2.4.1</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>浅色模式 Banner 遮罩大幅减淡：暗角、品红、晕影等渐变透明度全面降低，毛玻璃提亮，与浅色页面融为一体</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="primary" size="large">v2.4.0</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>播放清单全面改版为文件夹式UI：文件夹网格视图、封面缩略图预览、进入文件夹查看影片</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>跨文件夹移动影片：新增"移动到..."功能，可将影片从一个文件夹移动到另一个文件夹</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>文件夹操作：新建/重命名/删除文件夹，右键菜单快速操作</span>
            </li>
          </ul>
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>播放清单页面深浅主题全面适配，文件夹卡片 hover 发光效果</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>手机端完整适配：480px 以下 2 列布局，影片操作按钮常驻显示</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="warning" size="large">v2.3.5</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>浅色模式 Banner 全面适配：三层渐变遮罩、隐藏遮罩、指示器、毛玻璃模式等全部适配浅色主题，风格统一</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>手机端侧边栏底部空缺：打开菜单栏时自动锁定页面滚动，兼容 iOS/Android，关闭后恢复滚动位置</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v2.3.4</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>切换深浅模式导致屏蔽图片设置重置：后端用户设置保存改为合并模式，只更新传入字段不再覆盖未传入字段</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>浅色模式手机端 Header 未适配：改用更可靠的选择器，增加浅色边框和微阴影</span>
            </li>
          </ul>
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>设置页面 UI 全面升级：新增图标分区标头、卡片 hover 发光边框、居中布局、关于页行式排版</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>侧边栏新增"更新记录"入口，手机端也可方便访问</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>手机端设置页表单 label 防换行优化</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v2.3.3</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>下载进度实时更新：修复下载页面进度条不自动更新的问题，加入 WebSocket 自动重连和5秒轮询兜底机制，无需手动刷新即可看到实时进度</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>手机端设置页适配：修复“清除数据”对话框在手机上文字溢出问题，弹窗宽度自适应，按钮改为纵向排列</span>
            </li>
          </ul>
          <h3 class="section-title">体验优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>删除冗余提示：移除全局 API 响应成功提示、下载开始提示、刷新提示等无意义弹窗，仅保留用户需要确认操作的提示（如保存设置、收藏操作、清空数据等）</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v2.3.2</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>用户数据持久化：所有用户数据（收藏、稍后观看、观看历史、下载记录、封面等）统一存放到 DATA_ROOT 目录，Docker 部署只需挂载一个目录即可持久化全部数据，更新镜像不再丢失数据</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>代理设置持久化：通过设置页面修改的代理配置会自动保存到文件，重启后自动恢复，不再丢失</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>自动迁移：首次启动时自动将旧路径的数据迁移到新路径，无需手动操作</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v2.3.1</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>请求超时后全站不可用（根因修复）：CloudflareBypasser 失败时不再返回空值，改为抛异常，避免空结果被 lru_cache 缓存</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>lru_cache 缓存过滤增强：空字符串、空列表、空字典、全空字段的 Pydantic 模型均不被缓存</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>头像选择弹窗手机端适配：弹窗宽度自适应，封面网格改为2列</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="primary" size="large">v2.3.0</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>首页 Banner 电影级升级：多层渐变遮罩、Ken Burns 动画、发光播放按钮、胶囊指示器</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>视频卡片精致化：圆角 12px、微透明边框、品红微光悬停、毛玻璃徽章</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>视频分区样式升级：渐变发光竖条、胶囊按钮、品红半透明滚动条</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>顶部导航栏毛玻璃效果，滚动时更有层次感</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v2.2.0</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>扫描恢复下载记录：重新部署后自动从文件系统恢复丢失的记录</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>番剧分组视图：按番剧系列分组展示，显示封面、集数、进度</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>番剧详情弹窗：点击番剧卡片展开所有集，直接播放</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>下载搜索：按番剧名/文件名搜索下载记录</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>一键清除已完成/失败记录（不删除文件）</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>下载中心 UI 重构：搜索栏 + 列表/番剧视图切换</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>下载历史 API 支持搜索和过滤</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>番剧卡片手机端适配</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v2.1.5</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>全局防横向溢出，彻底消除手机端横向滚动条</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>AppHeader 手机端适配：小屏幕隐藏次要图标，缩小间距和字体</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>视频详情页手机端适配：操作按钮允许换行，缩小按钮和标签尺寸</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>首页视频分区手机端适配：横向滚动项目改为百分比宽度</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>搜索页和设置页手机端适配优化</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v2.1.4</el-tag>
          <span class="version-date">2026-07-16</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复搜索时满屏请求错误提示的问题，添加错误消息3秒节流</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复后端缓存空结果导致网站无法获取视频的核心问题（失败时不再缓存，返回503而非404）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复 token 过期时多个请求同时触发重复跳转登录页的问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复搜索加载更多失败后页码不回退导致跳页的问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复 API 端点函数名冲突问题</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>前端 axios 添加 30 秒超时，避免请求积压</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>后端 httpx 客户端超时从 60 秒减少到 30 秒</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>后端所有方法失败时抛出异常，确保错误结果不被缓存，重试可恢复</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>503 错误静默处理，不弹错误提示，由页面组件自行降级显示</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>全局异常响应码从 500 改为 503，区分内部错误与外部服务不可用</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v2.1.3</el-tag>
          <span class="version-date">2026-07-15</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>添加修改密码功能，在设置页面可修改用户密码</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span>稍后观看功能优化：观看后自动从列表移除，新增"开始观看"按钮</span>
            </li>
          </ul>
          <h3 class="section-title">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>区分收藏与稍后观看：收藏为永久标记，稍后观看为临时待看队列</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>用户密码从硬编码改为数据库存储，Docker重新部署不再丢失用户数据</span>
            </li>
          </ul>
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复观看历史功能未生效的问题，进入视频详情页自动记录观看历史</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复Docker重新部署后用户数据丢失的问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="warning" size="large">v2.1.2</el-tag>
          <span class="version-date">2026-07-15</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复内容屏蔽设置浏览器刷新后恢复默认的问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复收藏/稍后观看/播放清单 API 422 参数传递错误</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复旧数据库表缺少 username 列导致收藏等 API 500 错误</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复下载封面和用户头像不显示毛玻璃屏蔽效果</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复添加下载后需要手动刷新页面才能看到下载项的问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up" style="animation-delay: 0.1s;">
        <div class="section-header">
          <el-tag type="warning" size="large">v2.1.1</el-tag>
          <span class="version-date">2026-07-15</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复封面图片无法显示（改为通过 URL 查询参数传递认证 token）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复用户头像选择后无法显示</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复添加下载后下载列表不实时更新</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复内容屏蔽设置浏览器刷新后恢复默认</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>主题模式绑定用户：跨设备/浏览器保持一致</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><InfoFilled /></el-icon>
              <span>代理设置添加 Docker 环境 host.docker.internal 使用提示</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up" style="animation-delay: 0.1s;">
        <div class="section-header">
          <el-tag type="warning" size="large">v2.1.0</el-tag>
          <span class="version-date">2026-07-15</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><VideoPlay /></el-icon>
              <span>Banner 轮播图：首页 Banner 改为自动轮播，支持左右箭头和圆点指示器切换</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Star /></el-icon>
              <span>收藏功能：视频卡片快速收藏按钮，视频详情页收藏/稍后观看/加入播放清单</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><FolderOpened /></el-icon>
              <span>用户收藏夹实装：喜欢的影片、稍后观看、播放清单、观看历史全部可用</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">优化改进</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Calendar /></el-icon>
              <span>新番列表页面全新重设计：Tab 过滤器、卡片网格、彩色分类标题、展开动画</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>明亮模式优化：修复中间区域背景黑色，适配 Element Plus 全局组件样式</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><View /></el-icon>
              <span>毛玻璃模式优化：移除图标和"已屏蔽"文字，只保留模糊效果</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Search /></el-icon>
              <span>搜索结果标题提取优化：修复"最新上市"和"他们在看"无标题的问题</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复登录后侧边栏仍显示"未登录"</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复亮色模式下多个页面背景仍为黑色</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="danger" size="large">v2.0.0</el-tag>
          <span class="version-date">2026-07-15</span>
          <el-tag type="warning" size="small">重大更新</el-tag>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Key /></el-icon>
              <span>添加用户登录系统（JWT 认证），所有 API 需要登录后才能访问</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Lock /></el-icon>
              <span>未登录访问任何路由会自动跳转至登录页，防止爬虫扫描</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><View /></el-icon>
              <span>添加敏感图片屏蔽功能，支持毛玻璃打码和不显示图片两种模式（默认开启）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><User /></el-icon>
              <span>实现用户数据隔离，收藏、观看历史、下载记录等与用户绑定</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>设置页新增下载目录选择功能，支持绝对路径输入</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><FolderOpened /></el-icon>
              <span>设置页新增"打开目录"按钮，本地环境可打开文件管理器</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Refresh /></el-icon>
              <span>首页右上角新增刷新按钮，点击后清除缓存并重新获取推荐</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Refresh /></el-icon>
              <span>点击首页 Logo 时已在首页则触发刷新推荐内容</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Calendar /></el-icon>
              <span>全新日历/新番列表页面，按类型展示最新番剧</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Connection /></el-icon>
              <span>新增事件总线工具，实现跨组件通信</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Loading /></el-icon>
              <span>首页、日历页、轮播图等组件加载时显示骨架屏占位</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Star /></el-icon>
              <span>添加全局动画系统：路由切换、卡片悬停、交错入场等动画效果</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><InfoFilled /></el-icon>
              <span>在头部和设置页面显示当前版本号（v2.0.0）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Location /></el-icon>
              <span>代理地址输入时自动补全 http:// 前缀</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复搜索和查看更多页面只有预览图没有标题的问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Search /></el-icon>
              <span>修复搜索结果解析返回0个结果的问题，兼容多种页面结构</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复"最新里番"和"泡面番"的"查看更多"点击后无结果</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Calendar /></el-icon>
              <span>修复日历页面无法解析数据，改用搜索 API 构建新番列表</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>修复 DB_PATH 环境变量错误引用的问题</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 24px;">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><VideoPlay /></el-icon>
              <span>封面直接保存在番剧子目录中，优化封面查找逻辑</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>下载目录路径校验，兼容 Windows/Linux/Docker 环境</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><InfoFilled /></el-icon>
              <span>设置页新增 Docker 环境卷挂载说明</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up delay-200">
        <div class="section-header">
          <el-tag type="primary" size="large">v1.1.0</el-tag>
          <span class="version-date">2026-07-15</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">主要更新</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Cpu /></el-icon>
              <span>大幅优化内存占用，从 >1GB 降至约 65MB</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Delete /></el-icon>
              <span>移除 DrissionPage + Chromium 依赖，改用 BeautifulSoup + lxml</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Refresh /></el-icon>
              <span>移除 CF Bypass 服务依赖，简化部署配置</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Location /></el-icon>
              <span>使用 zhconv 替代 opencc，解决 Alpine 兼容性问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up delay-200">
        <div class="section-header">
          <el-tag type="success" size="large">v1.0.1</el-tag>
          <span class="version-date">2026-07-14</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复与优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复视频详情页 upload_date 验证错误</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><VideoPlay /></el-icon>
              <span>修复视频流 URL 为空导致无法播放和下载的问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Search /></el-icon>
              <span>添加从 JavaScript 中提取视频流 URL 的支持</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Setting /></el-icon>
              <span>修复 GitHub Actions 镜像标签大小写问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up delay-400">
        <div class="section-header">
          <el-tag type="warning" size="large">v1.0.0</el-tag>
          <span class="version-date">2026-07-13</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">初始版本</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加用户收藏系统（喜欢的影片）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加稍后观看列表功能</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加播放清单功能</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加观看历史记录</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加设置页面（代理配置、数据管理）</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>添加 GitHub Actions 自动构建多平台镜像</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Plus /></el-icon>
              <span>创建 NAS 专用 docker-compose.nas.yml</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复页面 404 问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复 Cloudflare 绕过问题</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><Warning /></el-icon>
              <span>修复页面内容解析问题</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up delay-500">
        <div class="section-header">
          <el-tag type="info" size="large">内存优化效果</el-tag>
        </div>
        <div class="section-content">
          <table class="optimization-table">
            <thead>
              <tr>
                <th>优化项</th>
                <th>优化前</th>
                <th>优化后</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>基础镜像</td>
                <td>python:3.10-slim (~200MB)</td>
                <td>python:3.10-alpine (~50MB)</td>
              </tr>
              <tr>
                <td>浏览器依赖</td>
                <td>DrissionPage + Chromium (~500MB+)</td>
                <td>BeautifulSoup + lxml (~20MB)</td>
              </tr>
              <tr>
                <td>容器内存限制</td>
                <td>无限制（>1GB）</td>
                <td>512MB</td>
              </tr>
              <tr>
                <td>简繁转换</td>
                <td>opencc (C 扩展)</td>
                <td>zhconv (纯 Python)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { Cpu, Delete, Refresh, Location, Warning, VideoPlay, Search, Setting, Plus, Key, Lock, View, Star, InfoFilled, User, FolderOpened, Calendar, Connection, Loading, SwitchButton, Picture, CircleCheck, SetUp } from '@element-plus/icons-vue';

export default defineComponent({
  name: 'ChangelogPage',
  components: {
    Cpu,
    Delete,
    Refresh,
    Location,
    Warning,
    VideoPlay,
    Search,
    Setting,
    Plus,
    Key,
    Lock,
    View,
    Star,
    InfoFilled,
    User,
    FolderOpened,
    Calendar,
    Connection,
    Loading,
    SwitchButton,
    Picture,
    CircleCheck,
    SetUp
  }
});
</script>

<style scoped>
.changelog-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--primary-color);
  margin: 0 0 10px 0;
}

.page-subtitle {
  color: var(--text-secondary-color);
  margin: 0;
}

.changelog-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.changelog-section {
  background-color: var(--bg-secondary-color);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark-color) 100%);
}

.version-date {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.section-content {
  padding: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--text-color);
}

.update-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.update-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.update-list li:last-child {
  border-bottom: none;
}

.update-list li:hover {
  padding-left: 12px;
  background-color: var(--hover-bg-color);
  border-radius: 6px;
}

.update-icon {
  color: var(--primary-color);
  flex-shrink: 0;
  margin-top: 2px;
}

.update-list li span {
  color: var(--text-color);
  font-size: 15px;
  line-height: 1.6;
}

.optimization-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.optimization-table th,
.optimization-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.optimization-table th {
  background-color: var(--bg-color);
  font-weight: 600;
  color: var(--text-secondary-color);
  font-size: 14px;
}

.optimization-table td {
  color: var(--text-color);
  font-size: 14px;
}

.optimization-table tbody tr:hover {
  background-color: var(--hover-bg-color);
}

/* PC端大气布局 */
@media (min-width: 769px) {
  .changelog-page {
    max-width: 1000px;
    padding: 40px 32px;
  }

  .page-title {
    font-size: 36px;
  }

  .page-header {
    margin-bottom: 48px;
  }

  .page-subtitle {
    font-size: 16px;
  }

  .changelog-container {
    gap: 36px;
  }

  .section-header {
    padding: 24px 28px;
  }

  .section-content {
    padding: 28px;
  }

  .section-title {
    font-size: 20px;
    margin-bottom: 24px;
  }

  .update-list li span {
    font-size: 16px;
  }

  .version-date {
    font-size: 15px;
  }
}

@media (max-width: 600px) {
  .changelog-page {
    padding: 20px 15px;
  }

  .page-title {
    font-size: 26px;
  }

  .section-header {
    padding: 16px 20px;
  }

  .section-content {
    padding: 20px 16px;
  }

  .optimization-table th,
  .optimization-table td {
    padding: 10px 12px;
    font-size: 13px;
  }
}
</style>