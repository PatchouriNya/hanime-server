# 修改记录文档

## 概述
本文档记录了本次对话中所有的修改内容，包括bug修复和新功能添加。

## 二十二、v3.0.0 多项bug修复 — v3.0.0 → v3.0.1 (2026-07-24)

### 修改原因
用户反馈5个问题：绿联影视中心列表封面模糊、登录页选择框换行、登出后头像不消失、图片屏蔽设置不记忆、下载目录设置不记忆。

### 修改内容

#### 1. 刮削封面模糊修复

**问题**：绿联影视中心预览列表封面模糊，点进详情才清楚。原因有两层：
1. 列表页将竖版 poster.jpg 压扁为横版缩略图显示，分辨率损失
2. 从网站下载的封面URL可能指向低分辨率缩略图

**文件：backend/app/services/scrape_service.py**
- tvshow.nfo 和 movie.nfo 中新增 `thumb aspect="landscape"` 声明，指向 `landscape.jpg`
- 新增 `generate_landscape()` 方法：生成横版缩略图
- 新增 `_crop_landscape_from_poster()` 方法：从竖版海报裁剪16:9中部横条
  - 竖版图：取中部16:9区域裁剪
  - 横版图：直接复制
- `_generate_tv_show_files()` 和 `_generate_movie_files()` 中新增调用 `generate_landscape()`
- `_download_cover_as_jpg()` 重写：
  - 新增 `_get_high_res_cover_urls()` 方法：从原始URL推断高分辨率版本（4种策略）
    - 策略1: /preview/ → /poster/
    - 策略2: /thumbnail/ → /
    - 策略3: 去掉URL尺寸参数（?w=320&h=180）
    - 策略4: 替换 _thumb/_small 后缀
  - 按优先级尝试高分辨率URL → 原始URL，选择分辨率最高的
  - 新增 `_get_image_resolution()` 方法：用Pillow检查图片分辨率
- `generate_poster()` 增强：
  - 检查已有 poster.jpg 分辨率，低于600px时尝试重新下载高分辨率版本
  - 兜底逻辑：URL下载失败时仍使用本地低分辨率封面

#### 2. 登录页选择框换行修复

**文件：frontend/src/views/LoginPage.vue**
- `.db-type-btn` 添加 `white-space: nowrap`，防止"本地数据库"文字换行

#### 3. 登出后头像不消失修复

**文件：frontend/src/App.vue**
- `handleLogout()` 中添加 `window.dispatchEvent(new Event('user-logout'))`，通知所有组件

**文件：frontend/src/components/AppSidebar.vue**
- 新增 `handleUserLogout()` 函数：登出时立即清除 `currentUsername`、`avatarUrl`、`selectedCoverId`
- `onMounted` 中监听 `user-logout` 事件

#### 4. 图片屏蔽设置不记忆修复

**问题**：`useContentSettings.ts` 中 `isInitialized` 是模块级变量，一旦为 true 就不再 `fetchSettings`。换设备或重新登录后不重新获取设置。

**文件：frontend/src/composables/useContentSettings.ts**（重写）
- 移除 `isInitialized` 模块级锁定
- 改为 `enableBlur.value === null` 时触发 `fetchSettings()`
- 监听 `user-login` 事件：重新获取设置
- 监听 `user-logout` 事件：重置为默认值
- 监听 `storage` 事件：跨标签页切换登录时同步

#### 5. 下载目录设置不记忆修复

**问题**：`set_download_dir` 只修改运行时 `settings.DOWNLOAD_PATH`，没有持久化到文件。重启/更新版本后恢复默认。

**文件：backend/app/config.py**
- 新增 `save_download_dir_to_file()` 函数：保存到 `download_dir_settings.json`
- 启动时新增从 `download_dir_settings.json` 恢复下载目录的逻辑

**文件：backend/app/api/endpoints/settings.py**
- `set_download_dir()` 中调用 `save_download_dir_to_file()` 持久化
- 修正 `COVER_PATH` 为 `new_path / "covers"`（原来是 `new_path`，封面不应和视频混放）
- 导入 `save_download_dir_to_file`

## 二十一、里番自动刮削功能 — v2.5.1 → v3.0.0 (2026-07-24)

### 修改原因
用户使用绿联4800plus NAS，下载的里番需要在影视中心中正确显示海报、简介、标签等元数据。绿联影视中心默认使用TMDB刮削，但TMDB对里番/成人动画覆盖极差，几乎无法识别。需要在下载完成后自动生成NFO元数据文件和JPG封面图片，让绿联影视中心通过读取本地NFO来显示完整的影片信息。

### 修改内容

#### 1. 新增文件

- `backend/app/models/scrape.py`：刮削相关Pydantic模型（ScrapeMode、ScrapeConfig、ScrapeRequest、BatchScrapeRequest、ScrapeResult、ScrapableSeries、NfoPreview）
- `backend/app/services/scrape_service.py`：刮削核心服务，包含：
  - NFO XML生成（tvshow.nfo / movie.nfo / episodedetails）
  - 封面图片下载和JPG格式转换
  - 文件重命名为S01E01格式
  - 目录重组为Season结构
  - 自动/手动/批量刮削流程
- `backend/app/api/endpoints/scrape.py`：刮削API端点（config/series/batch/preview/scan）
- `frontend/src/api/scrape.ts`：刮削前端API调用和TypeScript类型定义

#### 2. 修改文件

- `backend/app/config.py`：新增5个刮削配置项（SCRAPE_MODE、AUTO_SCRAPE_AFTER_DOWNLOAD、SCRAPE_RENAME_FILE、SCRAPE_REORGANIZE_DIRECTORY、SCRAPE_CONVERT_COVER_JPG）+ 刮削配置持久化恢复逻辑 + 版本号3.0.0
- `backend/app/api/routes.py`：注册 /api/scrape 路由
- `backend/app/services/download_service.py`：分段下载和单线程下载完成后触发自动刮削
- `backend/requirements.txt`：新增 Pillow~=10.4.0
- `frontend/src/views/Settings.vue`：新增"刮削"设置分区（模式选择、自动刮削、重命名、目录重组、封面转换、重要提示）
- `frontend/src/views/Downloads.vue`：新增"批量刮削"按钮和单个番剧"刮削"按钮
- `frontend/src/components/AppHeader.vue`：版本号3.0.0
- `CHANGELOG.md`：新增v3.0.0条目
- `ChangelogPage.vue`：新增v3.0.0条目

#### 3. 核心设计决策

- **利用项目自身数据**：项目已从hanime1.me获取完整元数据，无需额外外部数据源作为必须依赖
- **NFO兼容格式**：生成Kodi/Emby/Jellyfin兼容的NFO XML，绿联影视中心可读取
- **JPG强制转换**：绿联影视中心仅识别JPG格式封面（PNG不被识别），使用Pillow转换
- **NC-17分级**：成人内容自动标记，避免影视中心误归类
- **电视剧模式为默认**：里番通常为多集系列，最适合TV Show模式
- **文件重命名S01E01**：绿联影视中心依赖标准命名识别季集信息

## 二十、数据库表按命名规范重建 + 用户表专业化 — v2.5.0 → v2.5.1 (2026-07-17)

### 修改原因
用户指出初版设计未严格遵循 LibraryDream 命名规范，且 `user` 表字段过于简陋、不够专业。

### 修改内容

#### 1. 表名修正（遵循 `{namespace}_{entity}` 格式）
- `user` → `ld_user`：品牌共用表使用 `ld_` 前缀
- 外键列 `user_id` → `ld_user_id`：FK 列名与引用表名严格一致
- 索引名统一：`uk_ld_user_username`、`fk_hanime_user_favorite_ld_user` 等

#### 2. ld_user 表字段专业化扩展
新增字段：
- `email` VARCHAR(100) — 邮箱（唯一索引）
- `phone` VARCHAR(20) — 手机号
- `nickname` VARCHAR(50) — 昵称
- `real_name` VARCHAR(50) — 真实姓名
- `gender` TINYINT UNSIGNED — 性别: 1=男, 2=女, 3=其他
- `birth_date` DATE — 出生日期
- `bio` VARCHAR(200) — 个人简介
- `last_login_at` TIMESTAMP — 最后登录时间
- `last_login_ip` VARCHAR(45) — 最后登录IP（IPv6兼容）
- `user_type` TINYINT UNSIGNED, step 10 — 用户类型: 10=普通/20=管理员/30=超级管理员
- `status` TINYINT UNSIGNED, step 10 — 状态: 10=正常/20=禁用/30=封禁

移除字段：
- `is_active` — 由 `status` 统一管理（正常=10即代表激活）
- 保留 `avatar_url`、`is_deleted`、`deleted_at`

#### 3. 代码同步更新
- `mysql_user_service.py`：SQL 中 `user` → `ld_user`，`user_id` → `ld_user_id`，`is_active` → `status = 10`
- `config.py`：版本号 2.5.1
- 前端 `AppHeader.vue` / `Settings.vue`：版本 2.5.1

#### 4. 文档更新
- `CHANGELOG.md` / `ChangelogPage.vue`：新增 v2.5.1 条目

### 设计决策
- **枚举 step 10**：`user_type` 和 `status` 都从 10 开始，步进 10，便于未来在中间插入新类型
- **status 替代 is_active**：不使用独立的 `is_active` 布尔字段，状态字段统一表达激活/禁用/封禁
- **FK 名与表名一致**：`ld_user_id` 引用 `ld_user(id)`，让 SQL 自文档化
- **IPv6 兼容**：`last_login_ip` 使用 VARCHAR(45)，可以存储完整 IPv6 地址

## 十九、MySQL云数据库支持 — v2.4.3 → v2.5.0 大版本更新 (2026-07-17)

### 修改原因
用户需要将项目从纯本地 SQLite 数据库升级为支持远程 MySQL 云数据库，实现多项目共用同一套用户账号体系。

### 修改内容

#### 1. MySQL 数据库表结构创建（MCP MySQL）
在 `librarydream` 数据库中创建 7 张表：
- **`user`** — 多项目共用用户表：`id`(BIGINT PK)、`username`、`password_hash`、`nickname`、`avatar_url`、`is_active`、`is_deleted`、`created_at`、`updated_at`、`deleted_at`
- **`hanime_user_favorite`** — 收藏关联表：`user_id`(FK→user.id)、`video_id`、`title`、`cover_url`、`created_at`、唯一键(user_id, video_id)
- **`hanime_user_watch_later`** — 稍后观看关联表：同收藏表结构
- **`hanime_user_playlist`** — 播放清单表：`user_id`(FK)、`playlist_id`(UNIQUE)、`name`、`created_at`、`updated_at`
- **`hanime_user_playlist_video`** — 清单影片表：`playlist_id`(FK→playlist.playlist_id)、`video_id`、`title`、`cover_url`、`sort_order`、`created_at`、唯一键(playlist_id, video_id)
- **`hanime_user_watch_history`** — 观看历史表：`user_id`(FK)、`video_id`、`title`、`cover_url`、`progress`、`duration`、`watched_at`
- **`hanime_user_setting`** — 用户设置表：`user_id`(FK, UNIQUE)、`settings_data`(JSON)、`created_at`、`updated_at`

所有表使用 InnoDB 引擎、utf8mb4 字符集，外键级联删除，TIMESTAMP 字段有合适的默认值，状态字段使用 TINYINT UNSIGNED 而非 ENUM。

#### 2. 新增文件：`backend/app/services/mysql_user_service.py`
- `MySQLUserService` 类，基于 `aiomysql` 异步连接池
- 实现了与 `UserService` 完全对应的所有方法：认证、修改密码、收藏、稍后观看、播放清单（含视频管理）、观看历史、用户设置
- 播放清单在 MySQL 中拆分为清单表 + 清单视频表（规范化设计，不再存 JSON）
- 用户设置使用 JSON 类型字段，合并模式保存
- 使用 `ON DUPLICATE KEY UPDATE` 实现 upsert 语义

#### 3. 修改：`backend/app/config.py`
- 新增 5 个 MySQL 配置环境变量：`MYSQL_HOST`(默认127.0.0.1)、`MYSQL_PORT`(3306)、`MYSQL_USER`(root)、`MYSQL_PASSWORD`(空)、`MYSQL_DATABASE`(librarydream)
- 版本号更新至 2.5.0

#### 4. 修改：`backend/app/utils/auth.py`
- `get_current_user()` 返回值新增 `db_type`(默认"local") 和 `db_user_id` 字段
- JWT Token 在生成时包含 `db_type`，在验证时提取

#### 5. 修改：`backend/app/api/endpoints/auth.py`
- `LoginRequest` 模型新增 `db_type` 字段（默认"local"）
- `/login` 端点：`db_type=="cloud"` 时调用 `mysql_user_service.authenticate_user()`，`db_type=="local"` 时使用原有 SQLite 认证；云数据库认证失败时返回 503 而非 401
- `/change-password` 端点：根据 `user["db_type"]` 路由到对应的密码修改方法

#### 6. 修改：`backend/app/services/user_service.py`
- 所有方法添加 `db_type` 和 `db_user_id` 可选参数
- 每个方法开头检查：如果 `db_type=="cloud"` 且有 `db_user_id`，委托给 `mysql_user_service` 处理
- 原有 SQLite 逻辑不变，完全向后兼容
- 懒加载 `MySQLUserService` 实例

#### 7. 修改：`backend/app/api/endpoints/accounts.py`
- 新增 `_get_db_params(user)` 辅助函数提取 `db_type` 和 `db_user_id`
- 所有 19 个 API 端点在调用 `user_service` 方法时传入 `db_type` 和 `db_user_id`

#### 8. 修改：`frontend/src/views/LoginPage.vue`
- 表单上方新增数据库类型选择器：两个按钮（Monitor图标 + "本地数据库" / Cloudy图标 + "云数据库"），粉色高亮选中态
- 登录请求新增 `db_type` 字段
- 导入 `Monitor` 和 `Cloudy` 图标组件
- 选择器样式：圆角按钮组、毛玻璃背景、hover/active 状态过渡动画

#### 9. 配置更新
- `requirements.txt`：新增 `aiomysql~=0.2.0`
- `docker-compose.yml`：environment 新增 5 个 MySQL 变量映射
- `backend/.env.example`：新增 MySQL 配置段
- `CHANGELOG.md`：新增 v2.5.0 条目
- `ChangelogPage.vue`：新增 v2.5.0 条目（红色标签）

### 设计决策
- **FK字段命名**：所有外键列名与引用表名一致（如 `user_id` → `user.id`），遵循命名规范
- **共用用户表**：`user` 表不含任何项目特定字段，所有项目特色数据通过关联表存储，以项目前缀区分（如 `hanime_`）
- **双数据源并行**：不破坏原有 SQLite 功能，本地模式使用完全相同的 API，云模式透明切换
- **JWT 承载数据源信息**：token 中包含 `db_type` 和 `db_user_id`，后续请求自动路由到正确的数据库
- **aiomysql 连接池**：使用连接池管理 MySQL 连接，避免每次请求都创建新连接

## 十八、创建 LibraryDream 命名规范文档 — v1.0.0 → v2.0.0 重大升级 (2026-07-17)

### 创建原因
用户需要一套专业且有个性的命名规范，完全跳脱于现有项目，作为 LibraryDream 品牌的核心技术资产跨所有项目使用。用户明确指出不应参考现有项目代码风格。

### 第一版 (v1.0.0) — 初始创建
包含 15 章节，覆盖 MySQL、Python、TypeScript、Vue、CSS、文件、API、Git、魔数禁止、常量管理、版本号。

### 第二版 (v2.0.0) — 重大升级
根据用户反馈进行以下改进：

**1. 完全去项目化**
- 移除所有 hanime-server 特定引用
- 版本号同步位置改为通用描述（不再写具体文件路径）
- 示例从项目特定改为通用场景（如 `ld_blog` 代替 `ld_hanime`）

**2. 新增 4 个章节**
- **Redis 命名规范（第 5 章）**：Key 格式 `ld:{project}:{category}:{entity}:{id}`，13 种 Key 分类模板、数据结构选择指南、TTL 强制约定表、5 大禁用项
- **Docker 命名规范（第 12 章）**：镜像 `librarydream/{service}:{version}`、容器/网络/卷命名 `ld-{project}-{name}`、Compose 服务名、Dockerfile stage 命名
- **环境变量命名规范（第 13 章）**：格式 `LD_{SERVICE}_{KEY}`、通用变量、数据库变量、`.env` 文件约定
- **日志命名规范（第 14 章）**：文件命名 `{project}_{date}.log`、结构化日志 JSON 格式、字段命名约定

**3. 细节增强**
- 字段 COMMENT 强制规范（状态字段必须列出所有可能值）
- 数据库迁移文件命名 `{YYYYMMDDHHMMSS}_{description}.sql`
- Redis Key 命名规则（禁止动态前缀、禁止用户输入直接拼接、长度 ≤512）
- Redis Hash vs String 选择决策树
- 缩写列表新增 `ttl`、`rpc`，禁用列表新增 `mod`、`img`

**4. 目录结构更新**
- 从 15 章扩展到 19 章

### 创建内容（第二版新增）

**文件：NAMING_CONVENTION_AI.md**（新建，约 300 行）

AI 专用浓缩版命名规范，设计目标：
- **极致省 token**：约为人版的 20%，每一条都是纯规则指令
- **零解释**：没有"为什么"、没有"原因"、没有"说明"，只有"是什么"和"怎么做"
- **AI 友好格式**：严格结构化、紧凑表格、规则列表、代码模板
- **可直接作为 System Prompt 片段**：按章节注入 AI 上下文

AI 版文档包含 17 个紧凑板块，与人版完全对应：
Universal Rules → MySQL → Redis → Python → TypeScript → Vue → CSS → Files/Dirs → API → Docker → Env Vars → Logging → Git → No Magic Numbers → Constants → Versioning → Anti-Patterns

### 关键设计决策（不变）
- 数据库表名单数、`ld_` 品牌前缀
- API URL kebab-case 复数、JSON key camelCase
- 布尔 `is_`、时间 `_at`、主键 `BIGINT UNSIGNED`
- 金额 `DECIMAL`、状态枚举禁 MySQL ENUM
- 枚举值间隔 10，品牌前缀贯穿 MySQL (`ld_`)、Redis (`ld:`)、Docker (`ld-`)、环境变量 (`LD_`)

---

## 十七、版本 v2.4.1 - Banner浅色遮罩大幅减淡 (2026-07-16)

### 修改原因
浅色模式下 Banner 渐变遮罩仍然太深，与页面其他元素格格不入。

### 修改内容

**文件：frontend/src/components/BannerSlider.vue**
- 暗角梯度：`0.85/0.5/0.1` → `0.55/0.25/0.04`
- 品红渐变：`0.4/0.05/0.05` → `0.15/0/0.03`
- 晕影：`0.25` → `0.12`
- 底部面板：`0.5` → `0.3`
- 毛玻璃亮度：`0.9` → `0.95`
- 指示器/箭头透明度进一步降低

### 版本号更新
- 版本号 2.4.0 → 2.4.1
- `CHANGELOG.md`、`ChangelogPage.vue`：新增 v2.4.1 条目

## 十六、版本 v2.4.0 - 播放清单文件夹式UI大改版 (2026-07-16)

### 修改原因
播放清单页面设计简陋，无手机端适配，功能单一（只能创建/删除/重命名清单），无法跨清单移动影片。

### 修改内容

**新增功能1：文件夹式UI**

**文件：frontend/src/views/Playlists.vue** - 完全重写
- 主页视图：文件夹网格布局（`grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))`）
- 每个文件夹卡片包含：封面缩略图（前4个影片2x2网格）、文件夹名称、影片数量、更新时间
- 空文件夹显示大 Folder 图标占位
- 点击文件夹进入内部视图（`currentFolder` ref 切换）
- 内部视图：返回按钮 + 可编辑文件夹名 + 删除按钮、影片网格
- 影片卡 hover 显示移动/移除操作按钮（移动端常驻显示）
- 空状态：圆形图标背景 + 创建按钮引导
- 加载状态：旋转 Loading 图标

**新增功能2：跨文件夹移动影片**

**文件：backend/app/services/user_service.py**
- 新增 `move_video_between_playlists()` 方法：获取源清单视频信息 → 从源移除 → 添加到目标

**文件：backend/app/api/endpoints/accounts.py**
- 新增 `POST /api/accounts/me/playlists/move-video` 端点
- 参数：`from_playlist_id`、`to_playlist_id`、`video_id`

**文件：frontend/src/api/account.ts**
- 新增 `AccountApi.moveVideoToPlaylist()` 方法

**新增功能3：文件夹操作**

- 新建弹窗：带 Folder 图标前缀的输入框、空名禁用创建按钮
- 右键菜单（el-dropdown）：重命名 + 删除（红色危险标注）
- 内联重命名：文件夹名旁 Edit 按钮 → 点击变为 el-input → blur/enter 保存
- 删除确认弹窗：红色警告图标 + 不可撤销提示

**样式全面升级**

- `max-width: 1000px` 居中布局
- 标题加 `title-accent` 渐变装饰条
- 文件夹卡片 hover 边框发光 `var(--primary-color)` + `translateY(-2px)`
- 亮色模式独立 hover 阴影
- 文件夹封面 `linear-gradient` 底部渐变遮罩
- 内部视图 `fadeIn` 入场动画
- 移动选择列表 hover 高亮
- 时间显示：今天/昨天/月日 智能判断
- `font-size`、`gap`、`padding` 等全面调优

**手机端适配**

- 768px：文件夹 `minmax(160px)` / 影片 `minmax(130px)`、影片操作按钮常驻
- 480px：文件夹 `repeat(2, 1fr)` / 影片 `repeat(2, 1fr)`、字号缩小、间距收窄

### 版本号更新
- `backend/app/config.py`：APP_VERSION 2.3.5 → 2.4.0
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.4.0
- `frontend/src/views/Settings.vue`：版本号 v2.4.0
- `CHANGELOG.md`、`ChangelogPage.vue`：新增 v2.4.0 条目

## 十五、版本 v2.3.5 - 浅色模式Banner全面适配 + 侧边栏滚动锁定增强 (2026-07-16)

### 修改原因
1. 浅色模式下 Banner 三种状态（正常/毛玻璃/隐藏）均未完全适配
2. 手机端侧边栏滚动锁定在 iOS Safari 上不生效

### 修改内容

**修复1：浅色模式 Banner 全面适配（三轮迭代）**

**文件：frontend/src/components/BannerSlider.vue**
- 容器阴影改为 `rgba(0,0,0,0.1)`
- 空状态/骨架屏背景改为 `#e5e7eb`
- "图片已隐藏"遮罩改为浅灰渐变 `#f3f4f6 → #e5e7eb` + 深色文字图标
- 三层渐变遮罩透明度全面减弱（暗角 0.95→0.85, 0.7→0.5, 0.2→0.1；品红 0.6→0.4, 0.08→0.05；晕影 0.4→0.25）
- 底部信息面板渐变减弱（0.7→0.5）
- 胶囊指示器和导航箭头改为灰色半透明 `rgba(128,128,128,0.25)`
- 毛玻璃模式图片提亮（brightness 0.8 → 0.9）

**修复2：侧边栏滚动锁定增强（两轮迭代）**

**文件：frontend/src/App.vue**
- 第一轮：仅 `body overflow:hidden`（iOS 不生效）
- 第二轮：`html` + `body` 同时 `overflow:hidden` + `body position:fixed; width:100%`
- 打开时保存 `window.scrollY`，关闭后恢复 `window.scrollTo()`

**文件：frontend/src/components/AppSidebar.vue**
- `.sidebar-container` 新增 `height: 100dvh`

### 版本号更新
- 版本号保持 v2.3.5
- `CHANGELOG.md`、`ChangelogPage.vue`：更新条目内容

## 十四、版本 v2.3.4 - 深浅模式切换bug修复 + 设置页UI升级 + Header浅色适配 (2026-07-16)

### 修改原因
1. 切换深浅模式时屏蔽图片设置会重置为默认毛玻璃
2. 设置页样式不够高级，用户要求优化
3. 浅色模式下手机端 Header 没有适配
4. 手机端设置页 label 文字换行
5. 手机端侧边栏缺少更新记录入口

### 修改内容

**修复1：切换深浅模式屏蔽设置重置**

**文件：backend/app/services/user_service.py**
- `save_user_settings` 改为合并模式：先 `get_user_settings` 读出现有设置，`existing.update(settings)` 合并后再 `INSERT OR REPLACE`
- 根因：App.vue 切换主题时 `saveThemeToServer` 只传 `{ theme: 'light' }`，旧的 INSERT OR REPLACE 直接覆盖了整行，blur 设置被清空

**修复2：浅色模式 Header 适配**

**文件：frontend/src/components/AppHeader.vue**
- `:global(.light) .app-header` 改为 `html.light .app-header`（scoped CSS 中的 `:global()` 选择器不可靠）
- 亮色背景改为 `rgba(255, 255, 255, 0.9)`
- 新增 `border-bottom-color: #e5e7eb` 和 `box-shadow`

**优化：设置页 UI 全面升级**

**文件：frontend/src/views/Settings.vue**
- 布局改为居中卡片式（max-width 680px）
- 每个分区新增 `section-label`（图标 + uppercase 标题），隐藏原 `el-card__header`
- 卡片 hover 边框发光：`border-color: var(--primary-color)` + `box-shadow`
- 亮色模式卡片白色背景 + hover 阴影
- 关于页改为 `about-row` 行式排版（key-value 结构）
- 标题加 `title-accent` 渐变色装饰条
- 新增 `Hide`、`Lock` 图标导入
- 手机端 label 添加 `white-space: nowrap`

**新增：侧边栏更新记录入口**

**文件：frontend/src/components/AppSidebar.vue**
- "设置"下方新增"更新记录"导航项
- 导入并注册 `Document` 图标

### 版本号更新
- `backend/app/config.py`：APP_VERSION 2.3.3 → 2.3.4
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.3.4
- `frontend/src/views/Settings.vue`：版本号 v2.3.4
- `CHANGELOG.md`、`ChangelogPage.vue`：新增 v2.3.4 条目

## 十三、版本 v2.3.3 - 下载进度实时更新 + 冗余提示清理 + 手机端适配 (2026-07-16)

### 修改原因
1. 下载添加后进度条不实时更新，需手动刷新才能看到进度变化
2. 全站有很多无意义的成功提示弹窗（如搜索完弹"操作成功"），体验冗余
3. 手机端设置页"清除数据"区域文字溢出边框

### 修改内容

**修复1：下载进度实时更新**

**文件：frontend/src/stores/download.ts**
- `initializeDownloads`：移除"已初始化则跳过"的幂等检查，改为始终从API拉取最新数据，仅保留WebSocket连接的去重
- `refreshDownloads`：增加WebSocket自动重连逻辑（`if (!this.wsConnected) this.connectWebSocket()`）
- 新增 `startPolling()`/`stopPolling()` 方法：5秒间隔轮询作为WebSocket兜底
- 新增模块级 `_pollTimer` 变量

**文件：frontend/src/views/Downloads.vue**
- `onMounted` 中调用 `downloadStore.startPolling()`
- `onUnmounted` 中调用 `downloadStore.stopPolling()`

**修复2：删除冗余成功提示**

**文件：frontend/src/utils/request.ts**
- 移除全局响应拦截器中的 `ElMessage.success(response.data.message || '操作成功')`（所有API调用不再自动弹提示）

**文件：frontend/src/stores/download.ts**
- 删除 `startDownload` 中的 `ElMessage.success('开始下载')`
- 删除 `pauseAllDownloads` 中的 `ElMessage.success('已暂停所有下载')`
- 删除 `resumeAllDownloads` 中的 `ElMessage.success('已恢复所有下载')`

**文件：frontend/src/views/Downloads.vue**
- 删除 `refreshDownloadList` 中的 `ElMessage.success('已刷新')`

**文件：frontend/src/views/Settings.vue**
- 删除 `openDownloadDir` 中成功时的 `ElMessage.success('目录路径: ...')`

**文件：frontend/src/components/VideoDetailPage.vue**
- 删除下载开始时的 `ElMessage.success('开始下载视频')`
- 删除重下载时的 `ElMessage.success('开始重新下载')`

**修复3：手机端设置页适配**

**文件：frontend/src/views/Settings.vue**
- 清空数据确认弹窗 `width` 从固定的 `"30%"` 改为 `:width="isMobile ? '90%' : '480px'"`
- 新增 `isMobile` ref 和 resize 监听
- `.data-actions` 移动端CSS从 `flex-direction: row; flex-wrap: wrap` 改为 `flex-direction: column`
- `.data-actions .el-button` 移动端从 `flex: 1; min-width: 0` 改为 `width: 100%; margin-left: 0`

### 版本号更新
- `backend/app/config.py`：APP_VERSION 2.3.2 → 2.3.3
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.3.3
- `frontend/src/views/Settings.vue`：版本号 v2.3.3
- `CHANGELOG.md`、`ChangelogPage.vue`：新增 v2.3.3 条目

## 十二、版本 v2.3.2 - 用户数据持久化 (2026-07-16)

### 修改原因
用户反馈每次更新重新拉取镜像后，收藏、稍后观看等用户数据全部丢失。根因是 docker-compose.nas.yml 中数据目录挂载路径（/app/backend/data）与实际数据库路径（/app/backend/db）不匹配，导致数据库未被挂载到宿主机，容器重建后数据随容器一起删除。

### 修改内容

**文件：backend/app/config.py** - 数据路径统一
- 新增 `DATA_ROOT` 配置项：`Path(os.getenv("DATA_ROOT", str(backend_root / "data")))`
- `DB_PATH` 默认值改为 `DATA_ROOT / "db"`（旧：`backend_root / "db"`）
- `DOWNLOAD_PATH` 默认值改为 `DATA_ROOT / "downloads"`（旧：`backend_root / "downloads"`）
- `COVER_PATH` 默认值改为 `DATA_ROOT / "downloads" / "covers"`（旧：`backend_root / "downloads" / "covers"`）
- 使用 `pydantic.model_validator(mode='after')` 在环境变量未指定时使用 DATA_ROOT 默认路径，兼容旧配置
- 新增自动迁移逻辑：首次启动时检测旧路径（backend/db、backend/downloads），如有数据自动 move 到新路径
- 版本号 2.3.1 → 2.3.2

**文件：docker-compose.yml** - 简化挂载
- 旧：`./data/downloads:/app/backend/downloads` + `./data/db:/app/backend/db`（两个挂载）
- 新：`./data:/app/backend/data`（一个挂载持久化所有数据）

**文件：docker-compose.nas.yml** - 修正挂载路径
- 旧：`/volume1/docker/hanime/data:/app/backend/data` + `/volume1/docker/hanime/downloads:/app/backend/downloads`（data 挂载了但路径不含数据库）
- 新：`/volume1/docker/hanime/data:/app/backend/data`（一个挂载）

**文件：backend/.env.example** - 新增 DATA_ROOT
- 新增 `DATA_ROOT=/app/backend/data`
- 更新 `DOWNLOAD_PATH=/app/backend/data/downloads`

**文件：README.md** - 部署示例更新
- docker-compose 示例简化为单挂载
- mkdir 命令简化

**文件：frontend/src/components/AppHeader.vue** - 版本号 v2.3.2
**文件：frontend/src/views/Settings.vue** - 版本号 v2.3.2
**文件：frontend/src/views/ChangelogPage.vue** - 新增 v2.3.2 条目
**文件：CHANGELOG.md** - 新增 v2.3.2 条目

## 十一、版本 v2.3.1 - 修复请求超时后全站不可用 (2026-07-16)

### 修改原因
用户反馈严重bug仍未修复：切换菜单后突然报请求超时/错误，之后整个网站无法获取视频，播放视频提示没有可用的url流，首页所有地方都没有内容。此前已做两轮修复但问题仍在。同时用户指出更新记录从v2.1.5直接跳到v2.3.0，漏了v2.2.0版本号。

### 根本原因分析（第四轮深度排查）

**真正的根因不是空值缓存，而是 httpx AsyncClient 连接池污染**：

前几轮修复分别尝试了：
1. video_service 方法改为抛异常（不返回空对象）
2. API 端点移除 404 判断
3. cloudflare_bypass `_direct_*` 方法改为抛异常
4. cloudflare_bypass `get_request`/`post_request` 改为抛异常
5. lru_cache 增强空值过滤

但问题仍在。第四轮排查发现：当请求超时后，httpx `AsyncClient` 的 TCP 连接池中存在损坏/半开连接。CloudflareBypasser 是全局单例，`_direct_client` 只在与 `None` 或 `is_closed` 时重建。超时后的客户端既不是 None 也没关闭，被所有后续请求复用，导致"一连串全部失败"的症状。同时，并发请求中一个任务重置客户端后，其他任务仍持有旧引用导致 "client has been closed" 错误。

### 修改内容

#### 后端修改

**文件：backend/app/utils/cloudflare_bypass.py** - 核心修复（连接池清理）
- 新增 `_reset_direct_client()` 方法：关闭并清空 `_direct_client`，确保下次请求创建全新客户端
- 新增 `_reset_client()` 方法：关闭并清空 `_client`（CF bypass）同理
- `_direct_get_request`：所有重试耗尽后调用 `_reset_direct_client()` 再抛异常
- `_direct_post_request`：所有重试耗尽后调用 `_reset_direct_client()` 再抛异常
- `get_request`（CF bypass 模式）：所有重试耗尽后调用 `_reset_client()` 再抛异常
- `post_request`（CF bypass 模式）：所有重试耗尽后调用 `_reset_client()` 再抛异常
- **并发安全修复**：四个方法都将 `client = await self.xxx_client` 从方法级别移入重试循环内部，每次重试重新获取引用，避免并发任务间互相干扰

**文件：backend/app/utils/ttl_lru_cache.py** - 缓存过滤增强
- 新增 `_is_empty_result()` 辅助函数，检测以下无效结果：
  - `None`
  - 空字符串（`""` 或仅空格）
  - 空列表/空字典/空元组/空集合
  - Pydantic 模型所有字段都是默认空值（`model_dump()` 后全为 `None`/`""`/`[]`/`{}`/`0`）
- `async_wrapper` 和 `sync_wrapper`：缓存条件从 `if result is not None` 改为 `if not _is_empty_result(result)`
- 被跳过的缓存记录 `logger.warning` 级别日志

#### 版本号和更新记录修复

**问题**：更新记录从 v2.1.5 直接跳到 v2.3.0，缺少 v2.2.0

**文件：CHANGELOG.md**
- 在 v2.3.0 之前插入 v2.2.0（下载中心优化）和 v2.2.1（bug修复）条目
- v2.3.0 仅保留首页美化内容
- v2.2.0 包含下载中心的新增功能和优化

**文件：frontend/src/views/ChangelogPage.vue**
- 在 v2.3.0 之前插入 v2.2.1（红色danger标签）和 v2.2.0（绿色success标签）版本卡片
- v2.3.0 的"新增功能"部分（下载中心5项）移到 v2.2.0
- v2.3.0 保留首页美化4项优化

**文件：版本号更新**
- `backend/app/config.py`：APP_VERSION 2.3.0 → 2.3.1
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.3.1
- `frontend/src/views/Settings.vue`：版本号 v2.3.1

## 十、版本 v2.2.0 - 下载中心优化 (2026-07-16)

### 修改原因
用户反馈：重新部署后下载记录丢失（但文件还在）；下载列表越来越长无管理功能；需要搜索和分类展示。

### 修改内容

#### 后端修改

**文件：backend/app/services/download_service.py** - 新增5个方法
- `scan_and_restore_downloads(username)`：扫描下载目录，从文件名解析video_id，补建缺失的数据库记录
- `search_downloads(username, query, status)`：按标题/文件名搜索，按状态过滤
- `clear_completed_downloads(username)`：清除已完成记录（不删文件）
- `clear_failed_downloads(username)`：清除失败记录
- `get_download_groups(username)`：按番剧目录名分组，返回每组概要信息（封面、集数、大小、完成进度）

**文件：backend/app/api/endpoints/downloads.py** - 新增3个API端点
- `POST /downloads/scan`：扫描恢复
- `GET /downloads/groups`：获取番剧分组
- `GET /downloads/history` 扩展：新增 `search` 和 `status` 查询参数
- `POST /downloads/action` 扩展：新增 `clear_completed` 和 `clear_failed` 操作

#### 前端修改

**文件：frontend/src/api/download.ts** - 新增5个API方法
- `getDownloadHistory(search?, status?)`
- `getDownloadGroups()`
- `scanAndRestore()`
- `clearCompleted()`
- `clearFailed()`

**文件：frontend/src/views/Downloads.vue** - 完全重构
- 新增搜索栏（支持番剧名/文件名搜索）
- 新增列表/番剧视图切换
- 新增番剧分组视图：卡片网格布局，显示封面、集数、大小、进度
- 新增番剧详情弹窗：点击卡片展示所有集，可直接播放
- 新增"扫描恢复"按钮
- 新增"清除已完成"/"清除失败"按钮
- 保留原有列表视图的tab切换

#### 版本号更新
- `backend/app/config.py`：APP_VERSION 2.1.5 → 2.2.0
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.2.0
- `frontend/src/views/Settings.vue`：版本号 v2.2.0

## 十、版本 v2.3.0 - 首页美化 + 下载中心优化 (2026-07-16)

### 修改原因
用户反馈：首页Banner不够好看、整体不够高级；下载中心重新部署后记录丢失、列表越来越长、无搜索无分类。

### 修改内容

#### 首页 Banner 全面升级

**文件：frontend/src/components/BannerSlider.vue** - 完全重写
- 高度从 380px → 420px，圆角 8px → 16px
- 新增3层渐变遮罩：底部暗角、品红侧渐变、暗角晕影（电影感）
- 新增 Ken Burns 微缩放动画（8秒慢推）
- 播放按钮改为发光胶囊按钮（品红渐变 + 阴影光晕）
- 圆点指示器改为胶囊指示器（激活时展开为胶囊形，宽24px）
- 导航箭头添加 backdrop-filter 毛玻璃效果
- 标题信息从slide内移到底部独立面板，更流畅的切换

#### 视频卡片精致化

**文件：frontend/src/components/VideoCard.vue** - 样式重构
- 圆角从默认 → 12px，添加 1px 微透明边框
- 悬停时边框添加品红微光（border-color: rgba(236, 72, 153, 0.15)）
- 播放覆盖层从纯黑半透明 → 底部渐变遮罩，更自然
- 收藏按钮和徽章添加 backdrop-filter: blur(4px)
- 标题行高 1.3 → 1.4，间距优化

#### 视频分区样式升级

**文件：frontend/src/components/VideoSection.vue** - 样式重构
- 标题竖条改为渐变发光（linear-gradient + box-shadow）
- "查看更多"按钮改为胶囊圆角（border-radius: 20px）+ 渐变背景
- 滚动条优化为品红半透明（rgba(236, 72, 153, 0.3)）
- 分隔线改为微透明（rgba(255, 255, 255, 0.06)）
- 分区容器添加微边框和hover阴影加深

#### 顶部导航栏毛玻璃

**文件：frontend/src/components/AppHeader.vue**
- 背景色从 var(--bg-color) → rgba(24, 24, 27, 0.85) + backdrop-filter: blur(12px)
- 底部边框从 var(--bg-secondary-color) → rgba(255, 255, 255, 0.06)

#### 首页布局微调

**文件：frontend/src/components/HomePage.vue**
- padding 从 10px → 16px
- 骨架屏样式对齐新圆角和间距

#### 下载中心优化（后端+前端）

**文件：backend/app/services/download_service.py** - 新增5个方法
- scan_and_restore_downloads：扫描下载目录恢复记录
- search_downloads：搜索+过滤
- clear_completed_downloads/clear_failed_downloads：批量清理
- get_download_groups：按番剧分组

**文件：backend/app/api/endpoints/downloads.py** - 新增3个API
- POST /downloads/scan
- GET /downloads/groups
- GET /downloads/history 扩展（search/status参数）

**文件：frontend/src/api/download.ts** - 新增5个API方法

**文件：frontend/src/views/Downloads.vue** - 完全重构
- 新增搜索栏、列表/番剧视图切换
- 新增番剧分组视图（卡片网格）
- 新增番剧详情弹窗
- 新增扫描恢复、清除已完成/失败按钮

#### 版本号更新
- APP_VERSION 2.2.0 → 2.3.0
- AppHeader 版本徽章 v2.3.0
- Settings 版本号 v2.3.0

## 九、版本 v2.1.5 - 手机端适配优化 (2026-07-16)

### 修改原因
用户反馈手机端出现横向滚动条，体验不佳。需要全面适配手机端，让移动端体验更友好。

### 修改内容

#### 全局修改

**文件：frontend/src/assets/styles/common.css**
- 添加 `html, body { overflow-x: hidden; max-width: 100vw; }` 全局防横向溢出
- `.page-container` 添加 `overflow-x: hidden`

#### AppHeader 手机端适配

**文件：frontend/src/components/AppHeader.vue**
- 480px 以下：标题字体 18px，间距缩小到 6px，按钮 padding 4px，隐藏"更新日志"按钮，版本徽章缩小
- 360px 以下：标题字体 16px，隐藏"日历"按钮
- 原 480px 断点只有标题字体缩小，现在全面优化

#### VideoDetailPage 手机端适配

**文件：frontend/src/components/VideoDetailPage.vue**
- `.video-actions` 添加 `flex-wrap: wrap` 允许按钮换行（原来5个按钮排一行会溢出）
- 768px 以下：按钮间距 8px，按钮 padding 8px 12px，字体 13px
- 480px 以下：按钮间距 6px，按钮 padding 6px 10px，字体 12px，标签缩小

#### VideoSection 手机端适配

**文件：frontend/src/components/VideoSection.vue**
- 480px 以下：横向滚动项目宽度从 48% 改为 45%，最新项目从 120px 改为 32%
- 缩小 padding、间距、字体和"查看更多"按钮

#### SearchPage 手机端适配

**文件：frontend/src/components/SearchPage.vue**
- 768px 以下：搜索栏添加 padding 防贴边，网格间距 10px
- 480px 以下：搜索框字体 14px，高度 34px，按钮高度 34px
- 活跃过滤器区域允许换行

#### Settings 手机端适配

**文件：frontend/src/views/Settings.vue**
- 768px 以下：表单 label 宽度 100px，字体 13px
- 480px 以下：label 宽度 80px，字体 12px，按钮区域换行，提示文字缩小

#### 版本号更新
- `backend/app/config.py`：`APP_VERSION` 2.1.4 → 2.1.5
- `frontend/src/components/AppHeader.vue`：版本徽章 v2.1.5
- `frontend/src/views/Settings.vue`：版本号 v2.1.5
- `CHANGELOG.md`：添加 v2.1.5 记录
- `ChangelogPage.vue`：添加 v2.1.5 版本卡片

## 八、版本 v2.1.4 - 修复满屏请求错误和缓存空结果导致网站不可用 (2026-07-16)

### 修改原因
用户报告严重bug：在未知情况下（疑似搜索触发）会出现满屏请求错误/超时提示，之后整个网站无法获取视频。首次修复后用户反馈：虽不再满屏刷，但仍出现"请求地址出错"（404），之后整个网站又不可用。

### 根本原因分析（第二轮深入排查）
1. **lru_cache缓存404响应（最核心bug）**：`get_video_detail` 方法失败时返回空 `VideoDetail(video_id=video_id, title="")`，API端点判断 `not video` 为 True → 返回 **HTTP 404** → 404响应被 `@lru_cache` 缓存1小时！同理 `load_comments` 和 `load_replies` 返回空列表也被判断为"不存在"返回404并被缓存。这导致某个视频请求失败后，该视频在1小时内持续返回404。
2. **所有video_service方法都有此问题**：`get_home_data`、`get_search_combination`、`search_videos`、`get_video_detail`、`get_video_comments`、`get_comment_replies`、`get_calendar_data` 在失败时都返回空对象/空列表，被缓存后持续返回错误。
3. **前端错误消息无节流**：每个失败请求都弹 `ElMessage.error`，多请求并发时满屏错误。
4. **前端无请求超时**：axios 无 timeout + 后端 httpx 超时60秒 = 请求积压。
5. **401重复跳转**：token 过期时多个并发请求同时触发 `window.location.href = '/login'`。
6. **API函数名冲突**：`search_combination` 和 `search` 两个端点的处理函数同名 `search_videos`。

### 修改内容

#### 后端修改

**文件：backend/app/services/video_service.py** - 核心修改
- `get_home_data`：`page_content` 为空时抛异常；异常处理改为 `raise`
- `get_search_combination`：异常处理改为 `raise`
- `search_videos`：`page_content` 为空时抛异常；异常处理改为 `raise`
- `get_video_detail`：异常处理改为 `raise`（不再返回空VideoDetail）
- `get_video_comments`：异常处理改为 `raise`（不再返回空列表）
- `get_comment_replies`：异常处理改为 `raise`（不再返回空列表）
- `get_calendar_data`：异常处理改为 `raise`（不再返回CalendarData(error=...)）
- **效果**：异常穿透 `lru_cache`（不被缓存），下次请求会重新执行

**文件：backend/app/utils/ttl_lru_cache.py**
- `async_wrapper` 和 `sync_wrapper`：添加 `if result is not None` 检查，不缓存 None 结果

**文件：backend/app/api/endpoints/videos.py** - 重要重构
- `get_search_combination` 函数名修正（原与 `search_videos` 同名）
- 移除 `get_video_detail` 中的 `if not video: raise HTTPException(404)` 判断
- 移除 `load_comments` 中的 `if not comments: raise HTTPException(404)` 判断
- 移除 `load_replies` 中的 `if not replies: raise HTTPException(404)` 判断
- **效果**：不再有错误的404响应被缓存

**文件：backend/app/utils/cloudflare_bypass.py**
- `client` 和 `direct_client` 属性：httpx 超时从 60s → 30s

**文件：backend/main.py**
- 全局异常处理器：状态码从 500 → 503，消息改为"服务暂时不可用，请稍后重试"

**文件：backend/app/config.py**
- `APP_VERSION`：`"2.1.3"` → `"2.1.4"`

#### 前端修改

**文件：frontend/src/utils/request.ts** - 完全重写错误处理
- 错误消息节流：相同消息3秒内只显示一次
- `isRedirecting` 标志：防止401重复跳转
- `timeout: 30000`：30秒超时
- 超时错误单独处理（`ECONNABORTED`）
- **503静默处理**：不弹错误提示，由页面组件自行降级

**文件：frontend/src/api/video.ts**
- `getHomeData`/`refreshHomeData`：503时返回带 `error` 字段的空数据
- `banners` 类型修正：从 `BannerVideo` 对象改为 `[]` 空数组

**文件：frontend/src/components/SearchPage.vue**
- `loadMore`：保存 `previousPage`，失败时回退页码

**文件：frontend/src/components/AppHeader.vue**
- 版本徽章：`v2.1.3` → `v2.1.4`

**文件：frontend/src/views/Settings.vue**
- 版本号：`v2.1.3` → `v2.1.4`

**文件：frontend/src/views/ChangelogPage.vue**
- 更新 v2.1.4 版本卡片（5项修复 + 5项优化改进）

**文件：CHANGELOG.md**
- 更新 v2.1.4 记录（5项修复 + 5项优化改进）

### 测试验证
- lru_cache异常不缓存测试：✓ 通过（3个用例全通过）
- 后端启动测试：✓ 通过（所有路由正确注册）
- 前端构建测试：✓ 通过（vite build成功）

## 七、版本 v2.0.1 - 用户登出与头像功能 (2026-07-15)

### 需求描述
1. 侧边栏左上角支持用户登出
2. 修复"未登录"和"H1"硬编码显示问题，改为显示实际用户名和首字母
3. 用户头像功能：默认显示用户名首字母，点击可从已下载番剧封面中选择头像，不允许自定义上传

### 修改内容

#### 前端修改

**文件：frontend/src/components/AppSidebar.vue** - 重大重构
- 用户区域改为动态显示：登录后显示用户名，未登录显示"未登录"
- 默认头像：显示用户名首字母（如admin→A，lib→L），去掉原来的"H1"硬编码
- 添加登出按钮（红色，底部），点击后弹窗确认退出
- 头像点击弹出选择框，网格展示所有已完成下载的番剧封面
- 支持"恢复默认"和"确定选择"操作
- 头像存储为 avatar_video_id 到用户设置中，与用户绑定
- 新增图标：SwitchButton, Picture, Check

**文件：frontend/src/App.vue**
- 添加 handleLogout 函数处理登出（清除 localStorage 并跳转登录页）
- 向 AppSidebar 传递 logout 事件处理
- 引入 useRouter

**文件：frontend/src/components/AppHeader.vue**
- 版本号从 v2.0.0 更新为 v2.0.1

**文件：frontend/src/views/Settings.vue**
- 关于区域版本号更新为 v2.0.1

**文件：frontend/src/views/ChangelogPage.vue**
- 新增 v2.0.1 更新记录条目

**文件：backend/app/config.py**
- 版本号从 2.0.0 更新为 2.0.1

#### 文档文件
| 文件路径 | 修改内容 |
|---------|---------|
| CHANGELOG.md | 添加 v2.0.1 条目 |
| MODIFICATION_RECORD.md | 添加第七节记录 |

### 功能说明
- **头像选择流程**：点击侧边栏头像区域 → 弹出选择框 → 显示已下载番剧封面网格 → 选择→确定 → 保存到用户设置
- **登出流程**：点击底部退出登录 → 确认弹窗 → 清除token/username → 跳转/login
- **头像持久化**：存储在 /api/accounts/me/settings 的 avatar_video_id 字段，通过 /api/downloads/cover/{id} 加载

---

## 六、Git 冲突解决 (2026-07-15)

### 问题描述
由于忘记先 `git pull` 再进行修改，导致4个文件出现合并冲突。

### 冲突文件及解决方案

| 文件 | 冲突内容 | 解决方式 |
|------|---------|---------|
| CHANGELOG.md | 远程有v1.1.0内容，本地有v2.0.0内容 | 合并两者：v2.0.0在上，v1.1.0详细功能并入v2.0.0，保留旧版本记录 |
| backend/app/services/video_service.py | `_extract_based_video_info`方法中标题提取逻辑冲突 | 采用本地增强版：多种选择器+alt属性+兜底 |
| frontend/src/components/AppHeader.vue | 导入语句冲突（远程有mitt导入，本地有Document图标） | 保留两者：Document图标 + mitt事件总线 |
| frontend/src/components/BannerSlider.vue | img标签冲突（远程无模糊类，本地有模糊类绑定） | 采用本地版本：保留blurred class绑定 |

### 更新记录页面同步
- 更新 [ChangelogPage.vue](file:///c:/Users/Public/code/hanime-server/frontend/src/views/ChangelogPage.vue)，补充所有 v2.0.0 的新功能、修复、优化条目
- 新增图标导入：User, FolderOpened, Calendar, Connection, Loading

---


## 一、Bug修复：搜索和查看更多页面只有预览图没有标题

### 问题描述
用户反馈在"查看更多"页面和搜索结果页面中，部分视频卡片只有预览图但没有标题显示。

### 原因分析
原有的标题提取逻辑只使用了少数几种CSS选择器，无法覆盖所有页面结构。不同页面（首页、查看更多、搜索）的HTML结构可能不同，导致标题元素无法被正确定位。

### 修改内容

**文件：backend/app/services/video_service.py**

1. 扩展了标题选择器列表，增加了更多备选方案：
   - `home-rows-videos-title` 类
   - `card-mobile-title` 类
   - 包含 `title` 但不包含 `thumbnail` 和 `duration` 的div
   - span标签中的title类
   - h3、h4标签
   - 包含 `video-link` 类的a标签
   - 父级a标签

2. 添加了图片alt属性作为备选标题来源

3. 添加了视频ID作为最后的兜底标题

### 修改效果
现在能够正确提取各种页面结构下的视频标题，搜索和查看更多页面不再出现只有预览图没有标题的情况。

---

## 二、新功能：用户数据隔离

### 功能需求
- 所有用户设置（敏感图片屏蔽模式、默认值等）需要与用户绑定
- 下载记录、收藏、稍后观看、播放清单、观看历史等数据需要与用户绑定
- 切换账号后，新账号应使用初始默认值，不会看到其他用户的数据

### 实现方案

#### 后端修改

**文件：backend/app/services/user_service.py**

1. 修改所有数据库操作方法，添加 `username` 参数：
   - `add_favorite` / `get_favorites` / `remove_favorite`
   - `add_watch_later` / `get_watch_later` / `remove_watch_later`
   - `add_playlist` / `get_playlists` / `add_to_playlist` / `remove_from_playlist` / `delete_playlist`
   - `add_watch_history` / `get_watch_history` / `clear_watch_history`

2. 修改数据库表结构，添加 `username` 字段作为用户隔离标识

**文件：backend/app/services/download_service.py**

1. 修改下载记录相关方法，添加 `username` 参数：
   - `add_download` / `get_downloads` / `remove_download` / `clear_downloads`

**文件：backend/app/api/endpoints/accounts.py**

1. 更新所有API端点，添加认证依赖
2. 从JWT token中提取用户名，传递给服务层方法

#### 前端修改

**文件：frontend/src/composables/useContentSettings.ts**

1. 修改设置获取方式，从后端API获取当前用户的设置
2. 修改设置保存方式，将设置提交到后端API
3. 登录时自动加载用户设置，登出时清除本地设置

**文件：frontend/src/views/Settings.vue**

1. 修改设置加载逻辑，使用后端API数据
2. 修改设置保存逻辑，调用后端API

### 修改效果
- 每个用户有独立的设置和数据空间
- 切换账号后自动加载该账号的设置和数据
- 新账号首次登录时使用系统默认值

---

## 三、新功能：添加测试账号

### 需求描述
添加一个测试账号，用户名和密码都是 `lib`，用于内部测试。

### 修改内容

**文件：backend/app/utils/auth.py**

在 `VALID_USERS` 字典中添加测试账号：

```python
VALID_USERS = {
    "admin": "666666",
    "lib": "666666"
}
```

### 注意事项
- 该账号不写入README文档
- 仅用于内部测试目的

---

## 四、其他修改

### 版本号更新
**文件：backend/app/config.py**
- 版本号从 `1.0.0` 更新为 `2.0.0`

### 更新日志
**文件：CHANGELOG.md** 和 **frontend/src/views/ChangelogPage.vue**
- 添加了所有新功能和bug修复的记录

### 图标修复
**文件：frontend/src/views/LoginPage.vue** 和 **frontend/src/views/ChangelogPage.vue**
- 替换了Element Plus中不存在的图标：
  - `Sparkles` → `Star`
  - `Login` → `ArrowRight`
  - `Trash` → `Delete`
  - `Globe` → `Location`
  - `Bug` → `Warning`
  - `Wrench` → `Setting`
  - `Eye` → `View`
  - `ImageOff` → `Hide`

---

## 五、Docker测试验证

### 测试结果
- ✅ Docker构建成功
- ✅ 容器运行正常（端口7788）
- ✅ admin账号登录测试通过
- ✅ lib账号登录测试通过
- ✅ 认证状态API测试通过

### 测试命令
```powershell
# 构建并启动容器
docker-compose up --build -d

# 测试admin登录
Invoke-RestMethod -Uri http://localhost:7788/api/login -Method POST -ContentType 'application/json' -Body '{"username":"admin","password":"666666"}'

# 测试lib登录
Invoke-RestMethod -Uri http://localhost:7788/api/login -Method POST -ContentType 'application/json' -Body '{"username":"lib","password":"666666"}'
```

---

## 修改时间
2026年5月15日

---

## 相关文件清单

### 后端文件
| 文件路径 | 修改内容 |
|---------|---------|
| backend/app/services/video_service.py | 优化标题提取逻辑 |
| backend/app/services/user_service.py | 添加用户隔离字段 |
| backend/app/services/download_service.py | 添加用户隔离字段 |
| backend/app/api/endpoints/accounts.py | 更新API接口 |
| backend/app/utils/auth.py | 添加测试账号 |
| backend/app/config.py | 更新版本号 |

### 前端文件
| 文件路径 | 修改内容 |
|---------|---------|
| frontend/src/composables/useContentSettings.ts | 从后端获取设置 |
| frontend/src/views/Settings.vue | 使用后端API |
| frontend/src/views/LoginPage.vue | 修复图标 |
| frontend/src/views/ChangelogPage.vue | 更新日志、修复图标 |

### 文档文件
| 文件路径 | 修改内容 |
|---------|---------|
| CHANGELOG.md | 更新版本日志 |
| MODIFICATION_RECORD.md | 本文档 |