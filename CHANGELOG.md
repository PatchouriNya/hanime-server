# 更新日志

## v1.1.0 (2026-07-15)

### 新增功能

- **下载目录设置**：设置页新增下载目录选择功能，支持绝对路径输入（兼容 Windows/Linux/Docker 环境）
- **打开目录按钮**：设置页新增"打开目录"按钮，本地环境可直接打开文件管理器，Docker 环境显示路径信息
- **首页刷新按钮**：首页右上角新增刷新按钮，点击后清除后端缓存并重新获取推荐内容
- **Logo 刷新推荐**：点击首页 Logo 时，若已在首页则触发刷新推荐内容
- **新番列表页**：全新日历/新番列表页面，按类型（里番、泡面番、Motion Anime、3DCG 等）展示最新番剧
- **事件总线**：新增 mitt 事件总线工具，实现跨组件通信
- **骨架屏**：首页、日历页、轮播图等组件加载时显示骨架屏占位

### 修复

- **搜索结果解析**：修复搜索视频返回0个结果的问题，新增搜索结果页 HTML 结构解析（`_extract_search_result_video`），兼容多种页面结构
- **查看更多链接**：修复"最新里番"和"泡面番"的"查看更多"点击后无结果的问题
  - search_suffix 保留繁体原文，不再转为简体
  - 为"最新"类分区自动补充 `sort=最新上市` 参数
- **日历数据获取**：修复日历页面无法解析数据的问题，改用搜索 API 按类型构建新番列表
- **DB_PATH 环境变量**：修复 config.py 中 DB_PATH 错误引用 DOWNLOAD_PATH 环境变量的问题

### 优化

- **下载目录结构**：封面直接保存在番剧子目录中（`{video_id}.jpg`），不再单独创建 `covers/` 子目录
- **封面查找逻辑**：封面查找优先遍历番剧子目录，回退到全局封面目录，最后实时下载
- **下载目录路径校验**：
  - 新增 `_is_absolute_path` 函数，兼容 Windows（`C:\`）和 Linux（`/`）绝对路径
  - Linux/Docker 环境下输入 Windows 路径时给出明确提示
  - 自动去除路径末尾的斜杠
- **Docker 挂载提示**：设置页新增 Docker 环境卷挂载说明，docker-compose.yml 添加注释示例

### 文件变更

| 文件 | 变更说明 |
|------|----------|
| `backend/app/api/endpoints/downloads.py` | 封面查找逻辑优化，优先番剧目录 |
| `backend/app/api/endpoints/settings.py` | 新增下载目录设置、打开目录、清除缓存 API，路径校验 |
| `backend/app/api/endpoints/videos.py` | 新增首页缓存清除接口 |
| `backend/app/config.py` | 修复 DB_PATH 环境变量引用 |
| `backend/app/models/video.py` | 新增 CalendarData/CalendarDay 模型 |
| `backend/app/services/download_service.py` | 封面保存到番剧目录，移除 covers 子目录 |
| `backend/app/services/video_service.py` | 搜索结果解析修复，日历数据改用搜索 API，search_suffix 保留繁体 |
| `frontend/src/api/video.ts` | 新增刷新首页、日历数据 API |
| `frontend/src/components/AppHeader.vue` | Logo 点击刷新推荐 |
| `frontend/src/components/BannerSlider.vue` | 骨架屏适配 |
| `frontend/src/components/CalendarPage.vue` | 全新日历页，按类型展示，骨架屏 |
| `frontend/src/components/HomePage.vue` | 刷新按钮，骨架屏 |
| `frontend/src/types/video.ts` | 新增 CalendarData 类型 |
| `frontend/src/utils/mitt.ts` | 新增事件总线 |
| `frontend/src/views/Settings.vue` | 下载目录设置，打开目录，Docker 提示 |
| `docker-compose.yml` | 添加卷挂载注释示例 |
