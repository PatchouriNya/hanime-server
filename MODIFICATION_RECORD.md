# 修改记录文档

## 概述
本文档记录了本次对话中所有的修改内容，包括bug修复和新功能添加。

## 八、版本 v2.1.4 - 修复满屏请求错误和缓存空结果导致网站不可用 (2026-07-16)

### 修改原因
用户报告严重bug：在未知情况下（疑似搜索触发）会出现满屏请求错误/超时提示，之后整个网站无法获取视频。

### 根本原因分析
1. **lru_cache缓存空结果**：后端 `video_service.py` 的 `search_videos`、`get_search_combination`、`get_home_data` 方法在失败时返回空对象（如 `SearchResults()`、`HomeData(error=...)`），这些空结果被 `@lru_cache` 缓存（搜索缓存24小时，首页缓存30分钟），导致后续相同参数的请求持续返回空数据。
2. **前端错误消息无节流**：`request.ts` 中每个失败的请求都调用 `ElMessage.error`，多个请求同时失败时出现满屏错误提示。
3. **前端无请求超时**：axios 实例未设置 timeout，后端超时60秒期间前端持续等待，可能积累大量待处理请求。
4. **401重复跳转**：token 过期时多个并发请求同时触发 `window.location.href = '/login'`。
5. **loadMore失败跳页**：`SearchPage.vue` 的 `loadMore` 在请求前 `currentPage++`，失败后不回退，导致跳页。

### 修改内容

#### 后端修改

**文件：backend/app/services/video_service.py**
- `get_home_data`：`page_content` 为空时抛出异常而非返回 `HomeData(error=...)`；异常处理改为 `raise` 而非返回空对象
- `get_search_combination`：异常处理改为 `raise` 而非返回 `SearchCombination()`
- `search_videos`：`page_content` 为空时抛出异常而非返回 `SearchResults()`；异常处理改为 `raise` 而非返回空对象
- 效果：失败时异常向上传播，`lru_cache` 不会缓存异常，下次请求会重新尝试

**文件：backend/app/utils/ttl_lru_cache.py**
- `async_wrapper` 和 `sync_wrapper`：添加 `if result is not None` 检查，不缓存 None 结果

**文件：backend/app/utils/cloudflare_bypass.py**
- `client` 属性：`httpx.AsyncClient(timeout=60.0)` → `httpx.AsyncClient(timeout=30.0)`
- `direct_client` 属性：`httpx.AsyncClient(timeout=60.0, ...)` → `httpx.AsyncClient(timeout=30.0, ...)`
- 效果：加快失败检测，减少请求积压

**文件：backend/app/config.py**
- `APP_VERSION`：`"2.1.3"` → `"2.1.4"`

#### 前端修改

**文件：frontend/src/utils/request.ts** - 完全重写错误处理
- 添加错误消息节流：相同错误消息2秒内只显示一次（`showErrorMessage` 函数）
- 添加 `isRedirecting` 标志：防止401时多个请求同时触发跳转
- axios 实例添加 `timeout: 30000`（30秒超时）
- 添加超时错误单独处理（`ECONNABORTED`）

**文件：frontend/src/components/SearchPage.vue**
- `loadMore` 方法：保存 `previousPage`，失败时回退 `currentPage.value = previousPage`

**文件：frontend/src/components/AppHeader.vue**
- 版本徽章：`v2.1.3` → `v2.1.4`

**文件：frontend/src/views/Settings.vue**
- 版本号：`v2.1.3` → `v2.1.4`

**文件：frontend/src/views/ChangelogPage.vue**
- 添加 v2.1.4 版本卡片（4项修复 + 3项优化改进）

**文件：CHANGELOG.md**
- 添加 v2.1.4 更新记录

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