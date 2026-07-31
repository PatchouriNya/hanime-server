<template>
  <div class="changelog-page">
    <div class="page-header animate-fade-in-down">
      <h1 class="page-title">更新日志</h1>
      <p class="page-subtitle">记录项目的所有版本更新</p>
    </div>

    <div class="changelog-container">
      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.6.1</el-tag>
          <span class="version-date">2026-07-31</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>WebSocket 错误静默化：</strong>通过 HTTPS 域名访问时，外层反向代理若未配置 WebSocket Upgrade 转发，<code>wss://</code> 连接会失败并在控制台反复报错。现将 WebSocket 的 <code>onerror</code>/<code>onclose</code>/<code>onopen</code> 日志全部静默，最大重连次数从 10 降至 3，重连间隔从 1s 提升至 2s，避免控制台被错误刷屏。根因是外层反向代理（NAS/Cloudflare 等）需配置 <code>proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";</code> 才能转发 WebSocket。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.6.0</el-tag>
          <span class="version-date">2026-07-31</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>最新里番/查看更多页面空白：</strong>根因为 <code>_extract_search_result_video</code> 等3处视频提取方法中 <code>studio</code> 初始化为 <code>{}</code>（空字典），而 <code>VideoStudio.name</code> 是必填字段，导致 Pydantic 校验抛出 <code>ValidationError</code>。异常被 <code>try/except</code> 捕获后静默返回 <code>None</code>，所有未提取到发行商的视频都被丢弃，搜索结果为空。修复后将 <code>studio</code> 初始化为 <code>None</code>，未找到发行商时不再阻断视频提取。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.9</el-tag>
          <span class="version-date">2026-07-31</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>搜索/查看更多页不显示发行商：</strong>根因为 <code>_extract_search_result_video</code> 只提取了 video_id、cover_url、title 三个字段，未提取 studio。修复后同时提取发行商、时长、点赞率、播放量，搜索/查看更多页卡片信息与首页一致。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.8</el-tag>
          <span class="version-date">2026-07-31</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>显示发行商设置：</strong>新增全局设置开关，可控制视频卡片是否显示发行商信息。关闭后所有页面的视频卡片均不显示发行商，开启则统一显示（设置 > 内容屏蔽 > 显示发行商）。</span>
            </li>
          </ul>
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>搜索/查看更多页面统一卡片布局：</strong>搜索结果和"查看更多"页面合并为统一视频列表，使用横版封面网格卡片布局，替代旧的双列表分隔展示。卡片支持悬停动画、播放图标、发行商信息，视觉与主页一致。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>搜索结果响应式适配：</strong>PC端每行最多4列大卡片（280px），平板端自适应（200px），手机端紧凑布局（150px），各端间距和字号独立优化。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.7</el-tag>
          <span class="version-date">2026-07-29</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载管理分页：</strong>下载管理页全部视图（列表视图、番剧视图、详情弹窗、下载中/已完成/已失败tab）均支持分页，默认每页5条，可选5/10/20/50条。</span>
            </li>
          </ul>
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>切换菜单偶尔无响应：</strong>401拦截器的 <code>isRedirecting</code> 标志永不重置，导致首次401后后续会话过期无法正确跳转登录页；导航按钮 <code>router.push</code> 无错误处理，重复点击同一路径会抛异常。均已修复。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.6</el-tag>
          <span class="version-date">2026-07-29</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>综合评分算法：</strong>评分不再简单用好评率除以10（100%=10分太离谱）。新算法综合好评率、好评数量、播放量、评论数四个维度，通过贝叶斯平滑+幂函数压缩+对数缩放计算更有区分度的10分制评分。合集评分取所有集评分的平均值。例如：100%好评+10万赞+1000评论+5000万播放 → 9.8分，100%好评+1.2万赞+143评论+700万播放 → 9.6分，而只有10个好评的100%视频 → 7.2分。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>视频详情页评分显示优化：</strong>好评率旁新增综合评分数字，格式如"8.4 100% 好评 (1.2万)"，评分高亮显示更醒目。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.5</el-tag>
          <span class="version-date">2026-07-29</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>评分刮削提取错误：</strong>之前从视频详情页提取点赞率时，查找的是相关视频的 stats-container 结构，导致提取到的是相关视频的评分而非当前视频。修复后优先从 <code>video-like-btn</code> 按钮提取当前视频自己的点赞率，同时提取点赞人数。</span>
            </li>
          </ul>
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>视频详情页显示好评率：</strong>在观看次数和上传日期旁新增好评率及点赞人数显示，如"100% 好评 (1.2万)"。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.4</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>登录页弹出"拒绝访问"错误：</strong>未登录用户进入登录页时，页面组件发起的 API 请求返回 403/404 会弹出错误提示。修复后在登录页静默忽略这些错误，不再打扰用户。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.3</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>设为合集海报未同步 Season 目录：</strong>点击"设为合集海报"后只更新了根目录的 poster.jpg，但绿联 NAS 实际显示的是 Season 目录内的 poster.jpg，导致海报未实际生效。修复后同时更新所有 Season 目录内的 poster.jpg。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.2</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>列表视图按合集分组：</strong>下载中心列表视图改为可折叠合集分组，每个合集一行，点击展开查看每集详情。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>设为合集海报：</strong>在合集每集右侧新增"设为合集海报"按钮，点击后将该集封面更新为合集 poster.jpg。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>重新刮削按钮：</strong>列表视图合集行、番剧视图卡片、番剧详情弹窗顶部均新增"重新刮削"按钮。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.1</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>设置项精简：</strong>「合集海报使用第一集海报」精简为「合集首集海报」，语义不变，表达更简洁。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削评分修复：</strong>刮削出来的评分之前全都是7.6，因为视频详情页解析时没有提取点赞率字段，导致评分始终回退到默认值。现在从详情页中多策略提取每集点赞率（如 83% → 8.3 分），合集评分取所有集评分的平均值，NFO 评分反映真实数据。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.5.0</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>合集海报使用第一集海报：</strong>新增设置开关（默认开启）。开启后合集海报始终使用最早上传的剧集封面，关闭后使用首次下载的那集封面。</span>
            </li>
          </ul>
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削集号按上映时间排序：</strong>先下载第二集再下载第一集时，刮削后第一集的标题和简介会错误。修复后改为按上传日期排序。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>NFO 元数据索引错位：</strong>改为通过 video_id 精确查找元数据，避免错位。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.9</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削集号按上映时间排序：</strong>先下载第二集再下载第一集时，刮削后第一集的标题和简介会错误。修复后改为按上传日期排序，越早发布的集号越小。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>NFO 元数据索引错位：</strong>生成单集 NFO 时使用索引取元数据，集号重排后可能导致简介丢失或标题错乱。改为通过 video_id 精确查找，避免错位。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.8</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>智能轮询策略：</strong>下载页不再无脑每 5 秒轮询。改为仅在活跃下载时轮询（兜底 WebSocket），所有下载完成后自动停止轮询，新下载开始时自动恢复。空闲时零请求。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>WebSocket 智能连接：</strong>离开下载页时自动断开 WebSocket，回到时重连。切换标签页也智能断开/重连，减少不必要的长连接占用。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.7</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>服务莫名重启问题：</strong>移除 uvicorn 每 1000 个请求自动重启的限制。下载页轮询请求快速累积到 1000 导致服务频繁重启，已修复。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.6</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>同系列番剧按上映时间排序：</strong>无法从标题提取真实集号时，下载分配集号改为按上映日期排序，越早发布的集号越小。即使先下第二部再下第一部，集号也会按时间顺序正确排列。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>Nginx 性能优化：</strong>添加 Gzip 压缩（文本资源压缩率 60-80%），静态资源长缓存 1 年，SPA 入口不缓存确保最新版本，API 代理启用 Keep-Alive 连接复用减少 TCP 握手开销。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.5</el-tag>
          <span class="version-date">2026-07-28</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>首页加载速度优化：</strong>版本号信息合并到首页数据接口，减少一次 HTTP 请求。使用 localStorage 缓存版本号，页面加载时立即显示，不再出现 v0.0.0 闪烁。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.4</el-tag>
          <span class="version-date">2026-07-27</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>切换页面/刷新时提示"请求的资源不存在"：</strong>前端 404 错误提示增加请求 URL 信息便于定位。移除了会拦截 WebSocket 的全局 API catch-all 路由。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>WebSocket 断开时 ERROR 日志：</strong>浏览器刷新/切换页面时 WebSocket 断开是正常行为，改为 DEBUG 级别，不再刷屏。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>下载页轮询日志噪音：</strong>日志中间件过滤高频轮询请求（成功时静默），大幅减少日志量。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.3</el-tag>
          <span class="version-date">2026-07-27</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>颜色后缀剥离不全导致系列分裂：</strong>修复同系列视频因标题含中文颜色字符（黑/绿/蓝等）未被剥离而被识别为不同系列的问题。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>OVA/特典/番外不再映射为集号99：</strong>之前 OVA 标签固定映射为 E99，导致影视中心按范围分页（1-50/50-100）后需切换标签才能看封面。现在改为按下载顺序紧凑分配（E01/E02/E03/E04），所有集在一页可见。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.2</el-tag>
          <span class="version-date">2026-07-27</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>全站骨架屏 + shimmer 脉冲动画：</strong>首页、视频详情页、下载管理页、搜索页、收藏页全部替换为自定义 shimmer 动画骨架屏，加载时有明显的脉冲光效流动。</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 16px;">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>操作按钮在数据未加载时禁用：</strong>视频详情页所有操作按钮添加 <code>:disabled</code> 保护，下载管理页操作按钮在分组数据加载中禁用，防止"未找到下载链接"等报错。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.1</el-tag>
          <span class="version-date">2026-07-27</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>同系列视频并发下载集号冲突导致文件互相覆盖（严重 bug）：</strong>用户反馈下载 157878、404989、404990、157877 这 4 个 OVA 视频（同属"OVA ケガレボシ"系列）时，只能下出来 2 集，再下载其他 2 集会覆盖之前名字像的集。</span>
              <ul class="changelog-sublist">
                <li><strong>根因一</strong>：4 个视频标题都含 "OVA" 标签，集号提取都返回 99（OVA→99 是约定映射）</li>
                <li><strong>根因二</strong>：集号分配逻辑没有加锁，并发下载时都扫描到 <code>used_episodes</code> 为空，都分配 E99 互相覆盖</li>
                <li><strong>根因三</strong>：集号分配只扫描磁盘文件，没有查询数据库中正在下载但未完成的记录</li>
                <li><strong>修复</strong>：添加 <code>_episode_alloc_lock</code> 异步锁，集号分配 + filename 生成 + 数据库写入在同一个锁内原子完成；锁内额外查询数据库 <code>downloads</code> 表中同系列的下载记录</li>
                <li><strong>测试验证</strong>：Docker 容器内模拟 4 个 OVA 视频并发下载，分别分配到 E99/E100/E101/E102，集号唯一，文件名唯一，无覆盖</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.4.0</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>更新日志页面排版错乱：</strong>修复五类根因：</span>
              <ul class="changelog-sublist">
                <li>CSS 选择器 <code>.update-list li</code> 是后代选择器，会匹配嵌套子列表的 <code>&lt;li&gt;</code>，导致嵌套 li 被强行应用 flex 布局。改为 <code>.update-list &gt; li.update-item</code>（直接子选择器 + class 限定）</li>
                <li>多子元素时 flex row 让所有子元素横向排列。添加 <code>flex-wrap: wrap</code>，非 icon 子元素 <code>flex: 1 1 100%</code> 自动换行</li>
                <li>span 的 <code>flex-basis: auto</code> 按内容计算宽度导致换行。紧跟 icon 的 span 改用 <code>flex: 1 1 0</code> 强制按比例分配，确保和 icon 同行</li>
                <li>v3.3.4 section 错误使用 <code>changelog-list</code> class（应为 <code>update-list</code>），已统一为其他版本相同的样式</li>
                <li>历史版本号 <code>&lt;el-tag&gt;</code> 颜色五花八门（success/danger/warning/primary/默认五种混用），已统一为 <code>type="success"</code> 绿色</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.9</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新功能</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>简介自动翻译：</strong>刮削时自动翻译番剧简介到目标语言。新增翻译服务 <code>translation_service.py</code>，使用 Google Translate 公开端点（无需 API Key），支持长文本分段翻译，失败时保留原文不影响刮削。设置页"刮削"区块新增"自动翻译简介"开关 + "翻译目标语言"下拉，支持 <strong>简体中文（默认）/ 日文 / 英文 / 不翻译</strong>四种选项。设置持久化到 <code>db/scrape_settings.json</code>。</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 16px;">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>版本号统一管理：</strong>新增 <code>useVersion</code> composable 从后端 <code>/settings/version</code> 接口动态获取版本号，多组件共用缓存。设置页"关于"区块和页头徽章全部改用动态版本号，告别硬编码，避免每次升级遗漏同步。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>批量刮削进度反馈：</strong>用户反馈原"批量刮削"按钮点击后没反馈。重写为串行逐个刮削，新增进度对话框：实时显示总进度百分比、当前处理番剧、成功/失败计数、详细处理结果列表，单个失败不中断后续。同时把单请求超时从 30s 提升到 5~10min，避免大批量刮削超时。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复 NFO 进度反馈：</strong>新增进度对话框，扫描中显示加载状态，扫描完成显示扫描文件总数和修复文件数量。</span>
            </li>
          </ul>
          <h3 class="section-title" style="margin-top: 16px;">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>AppHeader 版本徽章显示 undefined：</strong>模板引用 <code v-pre>{{ displayVersion }}</code> 但 setup 未定义该变量，导致页面顶部徽章显示"undefined"。修复为正确使用 <code>useVersion</code>。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.8</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>单季合集不再显示"第1季"后缀：</strong>用户反馈，合集只有 1 季时显示"第1季"是冗余信息（比如"援助交配 第1季"看起来多余）。现在调整为：</span>
              <ul class="changelog-sublist">
                <li><strong>单季合集</strong>（total_seasons = 1）：season.nfo 的 title 直接用番剧名（如"援助交配"），不再加"第1季"</li>
                <li><strong>多季合集</strong>（total_seasons ≥ 2）：保持原行为，使用"第 N 季"格式（如"第1季"、"第2季"）</li>
              </ul>
              <span>sorttitle 字段同步调整，与 title 保持一致。合集层面的标题（tvshow.nfo 的 title）不受影响，始终是番剧名。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.7</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复部分老番剧集封面找不到竖版海报的问题：</strong>用户报告援助交配 (2020) 第8集（video_id=39468）刮出来的封面不是海报，被 v3.3.6 当作"源站没有竖版海报"处理。实际上源站<strong>有</strong>这集的海报（文件名 L3i9R0L.jpg），只是 <code>_get_cover_from_related_pages</code> 方法只遍历前 5 个相关视频的详情页，而 39468 这集要遍历到第 6 个相关视频（38387）才找到带 cover 的链接，导致前 5 个都失败后回退到 thumbnail。修复方案：</span>
              <ul class="changelog-sublist">
                <li>1. 将遍历范围从 5 个扩大到 30 个相关视频</li>
                <li>2. 一旦在某个相关视频页面找到 cover URL 立即返回，不浪费后续请求</li>
                <li>3. 新增直接 URL 拼接兜底：如果相关视频页面有指向当前视频的链接，尝试 <code>/image/cover/{video_id}.jpg</code> 直接 URL，并验证是否出现在页面源码中</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.6</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复部分剧集封面被强行拉伸变形：</strong>v3.3.5 把所有 <code>cover_url</code> 都按竖版海报放大到 1000x1426，但源站对部分老番（如援助交配第8集 video_id=39468）只提供横版 thumbnail 预览图（1024x576），导致横版图被强行拉伸为竖版变形。现在下载后先检测图像实际方向：</span>
              <ul class="changelog-sublist">
                <li>横版图（cover_url 实际是 thumbnail）→ 放大到 1920x1080 横版标准</li>
                <li>竖版图（真海报）→ 放大到 1000x1426 海报标准</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.5</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>每集封面改用该集自己的海报：</strong>之前 <code>generate_episode_thumb</code> 优先从视频文件截取画面作为每集封面，导致每集封面都是视频中间的某一帧，缺乏辨识度。现在调整优先级为：</span>
              <ul class="changelog-sublist">
                <li>1. 优先下载该集自己的 <code>cover_url</code>（竖版海报 268x394，放大到 1000x1426 标准海报尺寸）</li>
                <li>2. 回退到 <code>thumbnail URL</code>（横版高分辨率 1024x576）</li>
                <li>3. 最后兜底从视频文件截取画面</li>
              </ul>
              <span>同时新增 <code>force_regenerate</code> 参数，刮削时强制重新下载每集封面，确保使用最新的 <code>cover_url</code> 而非旧的截图。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.4</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>集号识别准确性大幅提升：</strong>下载和刮削时不再按"已有视频数量+1"顺序分配集号，改为从视频标题/副标题中提取真实集号。支持以下格式：</span>
              <ul class="changelog-sublist">
                <li>中文数字"第十一話"→11、"第二十話"→20、"第二十一話"→21（支持 1-99）</li>
                <li>阿拉伯数字"第2話"→2、"第15話"→15</li>
                <li>英文标记"Episode 5"、"Ep. 12"、"EP 3"</li>
                <li>"＃11"、"#5" 数字标记</li>
                <li>"Season N" 季号标记</li>
                <li>罗马数字"第Ⅱ"→2、"Ⅲ"→3</li>
                <li>文字标签"前編"→1、"中編"→2、"後編"→3、"上巻"→1、"下巻"→3、"OVA"→99</li>
                <li>末尾阿拉伯数字"援助交配 10"→10（自动排除 1900-2099 的年份）</li>
              </ul>
              <span>冲突时自动递增到下一个可用位置。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>系列识别修复：</strong>增强 <code>_extract_series_base</code>，处理标题中间的"第N話/话/期/章/部"集号标记。之前"○○交配 第一話 ..."和"○○交配 第十一話 ... 前編 [中文字幕]"会被识别为两个不同的系列，现在统一提取为基础名"○○交配 毎日お世話してくれる彼女はエルフのお姫様"。同时修复"Season N"末尾后缀被"末尾数字"规则误吞的问题。</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>刮削后清理空残留目录：</strong>新增 <code>_cleanup_empty_series_directories</code> 方法，刮削完成后扫描整个下载目录，自动清理：</span>
              <ul class="changelog-sublist">
                <li>完全空的残留目录（之前系列识别错误创建的目录，视频已被移走）</li>
                <li>仅含孤立附属文件（NFO/.jpg）但没有视频的目录</li>
              </ul>
              <span>解决"○○交配 第十一話 毎日お世話してくれる彼女はエルフのお姫様 前編 [中文字幕]"这类原始目录残留问题。</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.3</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">重构</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>根本性修复绿联NAS把同系列多季识别为独立剧集的问题：</strong>经过联网搜索绿联NAS影视中心合集识别机制的官方文档和论坛产品运营回复，发现真正的根因是"每集一季"策略导致每季只有 E01 一集，没有"剧集顺序"，NAS 无法判断这是剧集，被当成独立电影拆分。现在回归标准电视剧结构（参考"未来日记 (2011)"），所有同系列视频统一放入 Season 1 目录，文件名格式为 S01E01/S01E02/S01E03...，让绿联NAS 能通过"相似命名+剧集顺序"正确识别为剧集合集</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复 season.nfo 的 uniqueid 标签：</strong>之前每季使用不同的 video_id 作为 uniqueid，导致 NAS 把每季识别为独立剧集。现在所有 season.nfo 都使用同一个 series ID（tvshow.nfo 的 first_video_id），对齐"未来日记"参考格式：tvshow.nfo 和 season.nfo 使用相同的 series ID</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>每集独立海报通过 episode.jpg 实现：</strong>不再需要"每集一季"策略。每集的封面文件（番剧名 - S01E01 - 第 1 集.jpg，与视频同名）会被绿联NAS 自动识别为每集的小封面，在剧集详情页展示每集独立的海报</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.2</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>根本性修复绿联NAS把同系列多季识别为独立剧集的问题：</strong>season.nfo 中每个季的 uniqueid 标签使用了各自集的 video_id（如 Season 1=39710、Season 2=39937、Season 3=431），各季 uniqueid 不同导致绿联NAS 把每季识别为独立剧集。现在完全移除 season.nfo 中的 uniqueid 标签（对齐国色芳华参考格式），季的归属由目录结构和 seasonnumber 标签决定</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>移除 NFO 中 default="true" 属性：</strong>tvshow.nfo、episode.nfo、movie.nfo 的 uniqueid 标签之前带有 default="true" 属性，参考目录均无此属性，移除以完全对齐参考格式</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复 episodeguide 标签被 XML 转义的问题：</strong>minidom 格式化 XML 时会自动把 episodeguide 内容中的引号转义为 &quot;，导致 NAS 无法正确解析 series ID。现在恢复为原始 JSON 格式，对齐国色芳华和未来日记参考格式</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.1</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>彻底修复绿联NAS把同系列多季识别为独立剧集的问题：</strong>v3.3.0 把 {video_id}.jpg 移到 .covers/ 隐藏子目录后，NAS 仍然扫描该目录导致继续拆分。现在改为把封面文件移到中央封面目录（/downloads/covers/），这是系列目录的兄弟目录，NAS 不会将其识别为剧集。同时在封面目录放置 .nomedia 文件防止扫描，并自动清理旧的 .covers/ 目录</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.3.0</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复绿联NAS把同系列多季识别为独立剧集的问题：</strong>根目录中存在 {video_id}.jpg（如 39710.jpg、39937.jpg、431.jpg）等下载时保存的封面文件，绿联NAS扫描时可能将其当作独立视频文件，导致剧集被拆分为多个条目。现在刮削完成后会将这些文件移到 .covers/ 隐藏目录，既不影响NAS扫描，又保留后续刮削所需的封面数据</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复各季 Season 目录的预览图（landscape.jpg/thumb.jpg）完全相同的问题：</strong>旧逻辑只尝试从 thumbnail URL 下载横版预览图，但源站返回 HTTP 403 导致 Season 目录没有 landscape.jpg 和 thumb.jpg，绿联NAS 回退到根目录的同一张预览图。现在新增三级回退策略：优先从该季视频文件用 ffmpeg 截取真实画面（每集画面天然不同），失败则尝试下载，最后从该季竖版海报裁剪 16:9 横条</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.9</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复绿联NAS把同系列多季识别为独立剧集的问题：</strong>season.nfo 的 title 之前使用番剧名+集号（如"告白…… 1/2/3"），绿联NAS通过 title 模式识别为三部独立剧集。现在改回"第 N 季"格式（对齐梅林传奇参考格式），合集层面由 tvshow.nfo 的 title 显示番剧名，点开后显示"第 1 季"、"第 2 季"等，和梅林传奇的展示效果一致</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复标题栏版本号漏改：</strong>AppHeader.vue 的版本徽章从 v3.2.6 更新到 v3.2.9</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.8</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复每季 Season 目录的 poster.jpg 都相同的问题：</strong>旧逻辑直接从根目录复制 poster.jpg 到所有 Season 目录，导致每季海报都是第一次下载时的同一张图片。现在改为优先使用该季视频对应的 {video_id}.jpg（下载时保存的封面）生成 Season 目录的 poster.jpg，并放大到标准尺寸 1000x1426。season{NN}-poster.jpg 也同步使用该季独立的 poster，不再统一从根目录复制</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.7</el-tag>
          <span class="version-date">2026-07-26</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">新增</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>每集一季策略 + 番剧名作为季标题：</strong>参考"梅林传奇 (2008)"的目录结构，同系列番剧的每一集都独立放在一个 Season 目录中，让绿联NAS影视中心能为每集显示独立的海报。季标题（season.nfo 的 title）改为使用番剧名/副标题，不再使用"第N季"（如"援助交配 10"而非"第10季"），在 NAS 中浏览时看到的是番剧本身的名字，更直观</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>统一的集号提取方案（支持数字和文字标签）：</strong>新增文字标签到季号的语义映射表，无论标题是数字格式（"援助交配 10"）还是文字格式（"上卷"、"下卷"），都能正确提取季号。支持的文字标签：上卷/前篇→Season 1，中卷→Season 2，下卷/后篇→Season 3，OVA/特典/番外→Season 99。季号冲突时自动递增直到找到空闲数字</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>系列基础名提取支持文字标签后缀：</strong>"某番剧 上卷" → "某番剧"，"某番剧 下卷" → "某番剧"，确保同系列视频（无论数字还是文字标识）都能正确合并到同一番剧目录</span>
            </li>
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>目录整理支持文字标签季号：</strong>根目录残留的视频文件整理到 Season 子目录时，能正确识别"上卷/下卷"等标签分配季号</span>
            </li>
          </ul>
          <h3 class="section-title">优化</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>集号提取逻辑统一：</strong>首次下载的视频也会从标题提取季号（如"援助交配 10" → Season 10），不再默认归入 Season 1。同系列不同集的视频现在各自独立成季，每集都有独立的海报和元数据</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="success" size="large">v3.2.6</el-tag>
          <span class="version-date">2026-07-25</span>
        </div>
        <div class="section-content">
          <h3 class="section-title">修复</h3>
          <ul class="update-list">
            <li class="update-item">
              <el-icon class="update-icon"><CircleCheck /></el-icon>
              <span><strong>修复同系列番剧下载时季号分配错误：</strong>旧逻辑按 video_id 排序位置作为季号，导致同系列不同集的视频被错误分配到不同季（如"援助交配 10"和"援助交配 11"被分到 Season 3 和 Season 4）。现在改为从标题中提取季号信息（如"第2期"、"Season 2"），无季号标记时默认归入 Season 1，同系列视频正确合并到同一季</span>
            </li>
          </ul>
        </div>
      </div>

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
          <el-tag type="success" size="large">v3.1.1</el-tag>
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
          <el-tag type="success" size="large">v3.1.0</el-tag>
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
          <el-tag type="success" size="large">v3.0.9</el-tag>
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
          <el-tag type="success" size="large">v3.0.8</el-tag>
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
          <el-tag type="success" size="large">v3.0.6</el-tag>
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
          <el-tag type="success" size="large">v3.0.5</el-tag>
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
          <el-tag type="success" size="large">v3.0.4</el-tag>
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
          <el-tag type="success" size="large">v3.0.3</el-tag>
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
          <el-tag type="success" size="large">v3.0.2</el-tag>
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
          <el-tag type="success" size="large">v3.0.1</el-tag>
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
          <el-tag type="success" size="large">v3.0.0</el-tag>
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
          <el-tag type="success" size="large">v2.5.1</el-tag>
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
          <el-tag type="success" size="large">v2.5.0</el-tag>
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
          <el-tag type="success" size="large">v2.4.3</el-tag>
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
          <el-tag type="success" size="large">v2.4.2</el-tag>
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
          <el-tag type="success" size="large">v2.4.1</el-tag>
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
          <el-tag type="success" size="large">v2.4.0</el-tag>
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
          <el-tag type="success" size="large">v2.3.5</el-tag>
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
          <el-tag type="success" size="large">v2.3.4</el-tag>
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
          <el-tag type="success" size="large">v2.3.1</el-tag>
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
          <el-tag type="success" size="large">v2.3.0</el-tag>
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
          <el-tag type="success" size="large">v2.1.4</el-tag>
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
          <el-tag type="success" size="large">v2.1.2</el-tag>
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
          <el-tag type="success" size="large">v2.1.1</el-tag>
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
          <el-tag type="success" size="large">v2.1.0</el-tag>
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
          <el-tag type="success" size="large">v2.0.0</el-tag>
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
          <el-tag type="success" size="large">v1.1.0</el-tag>
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
          <el-tag type="success" size="large">v1.0.0</el-tag>
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

/* 直接子选择器 + class 限定，避免匹配嵌套 .changelog-sublist 里的 li */
.update-list > li.update-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;  /* 多子元素时允许换行，避免横向挤压 */
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.update-list > li.update-item:last-child {
  border-bottom: none;
}

.update-list > li.update-item:hover {
  padding-left: 12px;
  background-color: var(--hover-bg-color);
  border-radius: 6px;
}

.update-icon {
  color: var(--primary-color);
  flex: 0 0 auto;
  flex-shrink: 0;
  margin-top: 2px;
}

/* 默认所有非 icon 子元素占满整行（自动换行成块） */
.update-list > li.update-item > *:not(.update-icon) {
  flex: 1 1 100%;
  min-width: 0;
}

/* 紧跟 icon 的第一个 span 与 icon 同行（占剩余宽度） */
/* flex-basis: 0 强制按比例分配，避免内容过长时 flex-basis: auto 导致换行 */
.update-list > li.update-item > .update-icon + span {
  flex: 1 1 0;
}

/* 仅匹配直接子 span，不影响嵌套子列表内的 span */
.update-list > li.update-item > span {
  color: var(--text-color);
  font-size: 15px;
  line-height: 1.6;
}

/* 嵌套子列表样式（v3.3.4/v3.3.5/v3.3.6/v3.3.7/v3.3.8 中使用） */
.changelog-sublist {
  list-style: none;
  padding: 8px 0 8px 16px;
  margin: 8px 0;
  border-left: 2px solid var(--primary-color);
  background-color: var(--hover-bg-color);
  border-radius: 0 6px 6px 0;
}

.changelog-sublist li {
  color: var(--text-secondary-color);
  font-size: 14px;
  line-height: 1.7;
  padding: 4px 12px;
  position: relative;
}

.changelog-sublist li::before {
  content: '·';
  color: var(--primary-color);
  font-weight: bold;
  position: absolute;
  left: 2px;
}

/* PC端嵌套子列表字号略增 */
@media (min-width: 769px) {
  .changelog-sublist li {
    font-size: 15px;
  }
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

  .update-list > li.update-item > span {
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