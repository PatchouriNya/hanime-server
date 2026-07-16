<template>
  <div class="changelog-page">
    <div class="page-header animate-fade-in-down">
      <h1 class="page-title">更新日志</h1>
      <p class="page-subtitle">记录项目的所有版本更新</p>
    </div>

    <div class="changelog-container">
      <div class="changelog-section animate-fade-in-up">
        <div class="section-header">
          <el-tag type="primary" size="large">v2.3.0</el-tag>
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
            <li class="update-item">
              <el-icon class="update-icon"><SetUp /></el-icon>
              <span>下载中心 UI 重构：搜索栏 + 列表/番剧视图切换</span>
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