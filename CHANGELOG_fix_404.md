# 404问题修复记录

**日期**: 2026-07-14
**问题**: 部署后所有页面显示404，网站内容为空

---

## 第一轮修复：部署配置问题（5个修复）

### 1. nginx.conf 中 `server_name localhost` 限制访问
- **为什么修改**: `server_name localhost` 使得nginx只匹配Host头为"localhost"的请求。当用户通过IP地址（如192.168.x.x:7788）或域名访问时，请求无法匹配该server块，导致返回404。
- **修改内容**: 将 `server_name localhost` 改为 `server_name _`（匹配任意主机名），并在listen指令中添加 `default_server`。

### 2. Dockerfile 未删除nginx默认站点配置
- **为什么修改**: Debian系nginx安装后会自动创建 `/etc/nginx/sites-enabled/default` 默认站点配置，可能干扰请求路由。
- **修改内容**: 在Dockerfile中添加 `RUN rm -f /etc/nginx/sites-enabled/default`，同时增加前端构建产物验证步骤。

### 3. start.sh 使用 `service nginx start` 在Docker slim镜像中不可靠
- **为什么修改**: `service` 命令依赖init系统（systemd/sysvinit），Docker slim镜像中没有完整的init系统。`service nginx start` 可能失败，导致nginx未启动，所有请求返回404。
- **修改内容**: 将 `service nginx start` 替换为直接运行 `nginx` 命令。

### 4. docker-compose.yml 缺少 `build` 指令
- **为什么修改**: 原配置只有 `image: heisenyu/hanime-server:latest`，用户只能从Docker Hub拉取预构建镜像。如果镜像过期或有bug，用户无法用本地最新代码重新构建。
- **修改内容**: 在app服务中添加 `build: .` 指令。

### 5. api/download.ts 中 `createWebSocket` URL解析bug
- **为什么修改**: `new URL(baseUrl)` 对相对路径（如 `/api`）会抛出TypeError。
- **修改内容**: 移除有bug的URL解析逻辑，改为直接使用 `window.location.host` 构建WebSocket URL。

---

## 第二轮修复：cf-bypass 服务不可用导致API全部失败

**问题原因**: 后端所有数据请求（首页、搜索、视频详情等）都通过 `cf_bypasser` 发送，而 `cf_bypasser` 强依赖 cf-bypass 服务。当 cf-bypass 服务不可用时（镜像拉取失败、资源不足、崩溃等），所有API返回空数据，前端页面一片空白。

### 6. cloudflare_bypass.py：添加降级机制
- **为什么修改**: 当 cf-bypass 服务不可用时（`ConnectError`），后端完全没有 fallback 方案。
- **修改内容**:
  - 新增 `_bypass_available` 标记，追踪 bypass 服务的可用状态
  - 新增 `_direct_get_request` 和 `_direct_post_request` 方法，使用 httpx 代理直连
  - 在 `get_request` 和 `post_request` 中，当 bypass 连接失败时自动降级到代理直连模式
  - 当 `CLOUDFLARE_BYPASS_SERVICE_URL` 未配置时，直接使用代理模式
  - 当 bypass 可用后，`_bypass_available` 会恢复为 True

### 7. docker-compose.yml：cf-bypass 改为可选服务
- **为什么修改**: cf-bypass 需要 1G+ 内存和 Chrome 浏览器环境，很多 NAS/低配环境无法正常运行。
- **修改内容**:
  - cf-bypass 添加 `profiles: [bypass]`，默认 `docker-compose up` 不启动它
  - 需要 bypass 时使用 `docker-compose --profile bypass up -d`
  - `depends_on` 保持不变，当 bypass 未激活时 Docker Compose 会自动忽略
  - `USE_PROXY` 默认值从 `false` 改为 `true`（国内网络必须开代理）
  - `CLOUDFLARE_BYPASS_SERVICE_URL` 改为可通过环境变量控制

### 8. .env.example：更新代理配置说明
- **修改内容**: 添加 `CLOUDFLARE_BYPASS_SERVICE_URL` 配置项，明确标注 cf-bypass 为可选服务。

### 9. start.sh 中文字符编码导致 bash 解析失败
- **为什么修改**: 原 start.sh 包含大量中文注释和字符串（如"启动 Nginx 服务..."），这些中文字符在 Windows 上以 UTF-8 编码保存，但 Docker 构建时可能被错误处理，导致 bash 解析函数定义失败（`main: command not found`）。
- **修改内容**: 将所有中文替换为英文，确保脚本为纯 ASCII 编码，避免编码问题导致的运行时错误。

---

## 第三轮修复：代理模式下数据获取为空

**问题原因**: 虽然代理配置已启用，但数据仍无法获取。经过排查，发现以下三个问题：

### 10. DrissionPage 不支持代理
- **为什么修改**: DrissionPage 的 `SessionPage` 不支持通过环境变量或参数配置代理，导致即使设置了 `HTTP_PROXY` 环境变量，DrissionPage 请求仍然走直连，无法访问目标网站。
- **修改内容**: 在 `cloudflare_bypass.py` 中，当 `USE_PROXY=true` 时，直接使用 `httpx` 代理模式（`_direct_get_request`），跳过 DrissionPage。

### 11. 目标网站页面结构变化
- **为什么修改**: 目标网站 `hanime1.me` 的页面结构发生了变化，原来的视频容器类名从 `home-rows-videos-div` 变为 `video-item-container`，导致所有视频解析失败，返回空数据。
- **修改内容**:
  - 更新 `video_service.py` 中的 `_extract_based_video_info` 方法，支持新的 `video-link` 类名和 `title` div
  - 更新搜索功能中的视频元素选择器，从 `home-rows-videos-div` 改为 `video-item-container`

### 12. Accept-Encoding 导致压缩数据未解压
- **为什么修改**: 自定义请求头中包含 `Accept-Encoding: gzip, deflate, br`，但 httpx 在某些情况下没有正确解压响应，导致页面内容为乱码（压缩的二进制数据）。
- **修改内容**: 在 `cloudflare_bypass.py` 的 `direct_client` 配置中移除 `Accept-Encoding` 头，让 httpx 自动处理压缩。

---

## 第四轮修复：用户账户功能页面404

**问题原因**: 前端路由未配置"设置"、"稍后观看"、"喜欢的影片"、"播放清单"、"观看历史"等页面，后端缺少对应API端点，导致点击这些菜单时返回404。

### 13. 创建后端数据库模型 - 用户收藏、稍后观看、播放清单、观看历史
- **为什么修改**: 缺少数据库模型定义，无法存储用户数据。
- **修改内容**: 创建 `backend/app/models/user.py`，定义以下模型：
  - `UserVideoItem`: 用户视频项基础模型（video_id, title, cover_url, added_at）
  - `UserFavoriteItem`: 收藏视频项
  - `UserWatchLaterItem`: 稍后观看视频项
  - `PlaylistItem`: 播放清单视频项
  - `UserPlaylist`: 用户播放清单（含视频列表）
  - `WatchHistoryItem`: 观看历史项（含进度信息）
  - 各功能的响应模型（FavoritesResponse, WatchLaterResponse等）

### 14. 创建后端用户服务 - 实现CRUD操作
- **为什么修改**: 缺少业务逻辑层，无法操作数据库。
- **修改内容**: 创建 `backend/app/services/user_service.py`，实现以下功能：
  - 收藏管理：add_favorite, remove_favorite, get_favorites, is_favorite
  - 稍后观看：add_watch_later, remove_watch_later, get_watch_later, is_watch_later
  - 播放清单：create_playlist, delete_playlist, get_playlists, get_playlist, add_video_to_playlist, remove_video_from_playlist, update_playlist_name
  - 观看历史：add_watch_history, get_watch_history, clear_watch_history, remove_watch_history
  - 使用 aiosqlite 异步操作 SQLite 数据库

### 15. 创建后端API端点 - accounts路由
- **为什么修改**: 前端无法调用后端接口，数据无法交互。
- **修改内容**: 创建 `backend/app/api/endpoints/accounts.py`，提供以下API：
  - `GET/POST/DELETE /accounts/me/favorites`: 收藏增删查
  - `GET/POST/DELETE /accounts/me/watch_later`: 稍后观看增删查
  - `GET/POST/DELETE /accounts/me/playlists`: 播放清单增删查
  - `POST/DELETE /accounts/me/playlists/{id}/videos`: 播放清单视频增删
  - `PUT /accounts/me/playlists/{id}`: 更新播放清单名称
  - `GET/POST/DELETE /accounts/me/history`: 观看历史增删查

### 16. 注册后端路由到主应用
- **为什么修改**: 创建的路由未注册到FastAPI应用中，API无法访问。
- **修改内容**: 修改 `backend/app/api/routes.py`，添加accounts路由注册：`api_router.include_router(accounts.router, prefix="/accounts/me", tags=["用户账户"])`

### 17. 创建前端API客户端 - account.ts
- **为什么修改**: 前端缺少调用用户账户API的封装。
- **修改内容**: 创建 `frontend/src/api/account.ts`，提供 `AccountApi` 类，封装所有用户账户API调用。

### 18. 创建前端页面组件
- **为什么修改**: 缺少页面组件，路由无法匹配。
- **修改内容**:
  - 创建 `frontend/src/views/Favorites.vue`: 喜欢的影片页面，支持查看、删除、清空收藏
  - 创建 `frontend/src/views/WatchLater.vue`: 稍后观看页面，支持查看、删除、清空列表
  - 创建 `frontend/src/views/Playlists.vue`: 播放清单页面，支持创建、重命名、删除清单，添加/移除视频
  - 创建 `frontend/src/views/WatchHistory.vue`: 观看历史页面，支持查看进度、删除记录、清空历史
  - 创建 `frontend/src/views/Settings.vue`: 设置页面，支持代理配置、数据管理（清空/导入/导出）

### 19. 添加前端路由配置
- **为什么修改**: 路由未配置，导航到这些页面时返回404。
- **修改内容**: 修改 `frontend/src/router/index.ts`，添加以下路由：
  - `/favorites`: 喜欢的影片
  - `/watch-later`: 稍后观看
  - `/playlists`: 播放清单
  - `/history`: 观看历史
  - `/settings`: 设置

### 20. 修复侧边栏导航链接
- **为什么修改**: AppSidebar.vue中"稍后观看"的链接错误指向了`/history`。
- **修改内容**: 将链接从 `/history` 改为 `/watch-later`。

---

## 修改的文件汇总

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `frontend/nginx.conf` | 修改 | server_name改为_，添加default_server |
| `Dockerfile` | 修改 | 删除默认站点配置，增加构建产物验证 |
| `start.sh` | 修改 | nginx启动方式从service改为直接运行；中文字符替换为英文避免编码问题 |
| `docker-compose.yml` | 修改 | 添加build指令，cf-bypass改为可选，USE_PROXY默认true |
| `frontend/src/api/download.ts` | 修改 | 修复createWebSocket URL解析bug |
| `backend/app/utils/cloudflare_bypass.py` | 重写 | 添加bypass降级机制，不可用时自动用代理直连；代理模式下跳过DrissionPage；移除Accept-Encoding头 |
| `backend/app/services/video_service.py` | 修改 | 更新视频解析选择器适配新页面结构 |
| `.env.example` | 修改 | 更新代理和bypass配置说明 |
| `backend/app/models/user.py` | 新增 | 用户账户数据模型定义 |
| `backend/app/services/user_service.py` | 新增 | 用户服务CRUD实现（SQLite） |
| `backend/app/api/endpoints/accounts.py` | 新增 | 用户账户API端点 |
| `backend/app/api/routes.py` | 修改 | 注册accounts路由 |
| `frontend/src/api/account.ts` | 新增 | 前端用户账户API客户端 |
| `frontend/src/views/Favorites.vue` | 新增 | 喜欢的影片页面 |
| `frontend/src/views/WatchLater.vue` | 新增 | 稍后观看页面 |
| `frontend/src/views/Playlists.vue` | 新增 | 播放清单页面 |
| `frontend/src/views/WatchHistory.vue` | 新增 | 观看历史页面 |
| `frontend/src/views/Settings.vue` | 新增 | 设置页面 |
| `frontend/src/router/index.ts` | 修改 | 添加新页面路由 |
| `frontend/src/components/AppSidebar.vue` | 修改 | 修复导航链接 |

---

## 第五轮修复：后端启动失败（事件循环问题）

**问题原因**: `user_service.py` 在模块导入时（`user_service = UserService()`）就调用了 `asyncio.create_task()`，但此时还没有事件循环，导致后端服务启动失败。

### 21. 修复 UserService 初始化方式
- **为什么修改**: 在没有事件循环的情况下调用 `asyncio.create_task()` 会抛出 `RuntimeError: no running event loop`。
- **修改内容**: 修改 `backend/app/services/user_service.py`：
  - 将 `asyncio.create_task(self.init_db())` 从 `__init__` 中移除
  - 添加 `initialize()` 方法，在应用启动时由 lifespan 事件调用

### 22. 在应用启动时初始化用户服务
- **为什么修改**: 用户服务需要在事件循环启动后才能初始化。
- **修改内容**: 修改 `backend/app/main.py`：
  - 在 imports 中添加 `from app.services.user_service import user_service`
  - 在 lifespan 中添加 `await user_service.initialize()` 调用

### 验证结果

| 测试项 | 结果 |
|--------|------|
| 后端服务启动 | ✅ 成功 |
| `/api/accounts/me/favorites` API | ✅ 返回 200 |
| `/api/settings/proxy` API | ✅ 返回当前代理设置 |
| `/api/settings/proxy/test` API | ✅ 代理测试功能正常 |
| `/favorites` 页面 | ✅ 返回 200 |
| `/watch-later` 页面 | ✅ 返回 200 |
| `/playlists` 页面 | ✅ 返回 200 |
| `/history` 页面 | ✅ 返回 200 |
| `/settings` 页面 | ✅ 返回 200 |

---

## 第六轮修复：代理测试功能

**问题**: 用户无法验证代理是否正常工作。

### 23. 后端新增代理测试API
- **修改内容**: 修改 `backend/app/api/endpoints/settings.py`，新增 `GET /api/settings/proxy/test` 端点
- **功能**: 通过代理连接外部网站（Google/Baidu）验证代理是否生效，返回延迟时间

### 24. 前端设置页面添加测试按钮
- **修改内容**: 修改 `frontend/src/views/Settings.vue`
- **功能**: 
  - 添加"测试代理"按钮
  - 显示测试结果（成功/失败状态）
  - 显示代理延迟时间

---

## 部署方式

### 方式1：仅用代理（推荐，最简单）

创建 `.env` 文件：
```env
USE_PROXY=true
PROXY_URL=http://your-proxy-host:port
```

然后运行：
```bash
docker-compose up -d
```

### 方式2：使用 cf-bypass（需要较大内存）

```bash
docker-compose --profile bypass up -d
```

### 方式3：重新构建后部署

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 方式4：部署到ARM64设备（如绿联NAS）

**重要**: 绿联NAS 4800Plus 是 ARM64 架构，在 x86_64 电脑上构建的镜像无法在NAS上运行，会报 `exec format error`。

### 方式5：NAS一键部署（推荐）

通过 GitHub Actions 自动构建多平台镜像（amd64 + arm64），NAS上只需简单命令即可部署。

#### 步骤1：上传代码到GitHub

1. 创建一个新的GitHub仓库（私有仓库即可）
2. 推送代码：

```bash
cd /path/to/hanime-server
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/hanime-server.git
git push -u origin main
```

#### 步骤2：配置GitHub Actions（已内置）

项目已包含 `.github/workflows/docker-build.yml`，推送代码到 `main` 分支后会自动：
- 构建多平台镜像（amd64 + arm64）
- 推送到 GitHub Container Registry (ghcr.io)

#### 步骤3：NAS上一键部署

SSH登录NAS后执行：

```bash
# 创建部署目录
mkdir -p /volume1/docker/hanime-server
cd /volume1/docker/hanime-server

# 下载docker-compose.nas.yml（或手动创建）
curl -O https://raw.githubusercontent.com/your-username/hanime-server/main/docker-compose.nas.yml

# 登录ghcr.io（需要GitHub Personal Access Token）
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u your-username --password-stdin

# 拉取镜像并启动
docker-compose -f docker-compose.nas.yml pull
docker-compose -f docker-compose.nas.yml up -d
```

#### 步骤4：访问服务

打开浏览器访问 `http://你的NAS_IP:7788`

#### 步骤5：配置代理（可选）

进入设置页面，开启代理并填写代理地址（如 `http://192.168.1.xxx:7890`）。

### 方式6：手动构建部署（旧方式）

**推荐方式**: 在NAS上直接构建

```bash
# SSH登录NAS后执行
cd /path/to/hanime-server
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**备用方式**: 使用 buildx 跨平台构建（需要在电脑上配置好 buildx）

```bash
# 在电脑上构建ARM64镜像
docker buildx build --platform linux/arm64 -t heisenyu/hanime-server:arm64 .

# 导出镜像
docker save heisenyu/hanime-server:arm64 -o hanime-server-arm64.tar

# 将tar文件传输到NAS后导入
docker load -i hanime-server-arm64.tar

# 在NAS上启动
docker-compose up -d
```
