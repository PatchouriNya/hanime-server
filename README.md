# Hanime Server

<div align="center">
  <a href="https://github.com/heisenyu/hanime-server">
    <img src="img/logo.png" alt="Hanime Server Logo" width="120" style="margin-bottom: 20px;"/>
  </a>
  <br>
  
  [![GitHub Stars](https://img.shields.io/github/stars/heisenyu/hanime-server?style=flat&color=fc4c02)](https://github.com/heisenyu/hanime-server/stargazers)
  [![Docker Pulls](https://img.shields.io/docker/pulls/heisenyu/hanime-server?color=339933)](https://hub.docker.com/r/heisenyu/hanime-server)
  [![Docker Image Size](https://img.shields.io/docker/image-size/heisenyu/hanime-server)](https://hub.docker.com/r/heisenyu/hanime-server)

  <p>🎬 强大而简洁的Hanime视频浏览与下载解决方案</p>
</div>

<p align="center">
  <a href="#-功能特色">功能特色</a> •
  <a href="#-项目截图">项目截图</a> •
  <a href="#️-技术架构">技术架构</a> •
  <a href="#-部署指南">部署指南</a> •
  <a href="#-免责声明">免责声明</a> •
  <a href="#-许可证">许可证</a>
</p>


## 📜 项目简介

Hanime Server 是一个基于 Python 和 Vue.js 开发的全栈应用，用于浏览和播放 hanime 视频资源。项目采用前后端分离架构，后端使用 FastAPI 提供 RESTful API 接口，前端使用 Vue.js 构建响应式用户界面，支持多平台访问。

整个应用通过 Docker 容器化技术实现一键部署，大大简化了安装和使用流程。适合在NAS设备（如群晖、威联通、绿联等）上部署，可作为家庭媒体服务器使用，支持远程访问和视频管理。

> **关于作者**: 作者并非Vue开发者，前端主要借助Cursor AI辅助工具进行开发，如有不足之处，敬请谅解。
> 
> **项目灵感**: 本项目的页面布局和功能设计参考了 [YenalyLiew/Han1meViewer](https://github.com/YenalyLiew/Han1meViewer) Android端应用。由于原项目已标记为不再维护，促使我开发了这个基于Web的替代版本，让更多设备都能方便使用。本项目支持直接下载视频到NAS存储设备，便于媒体库集中管理和随时观看。

---

## 🔗 项目说明

本项目基于 [heisenyu/hanime-server](https://github.com/heisenyu/hanime-server) 进行维护和更新。

- **原项目地址**: https://github.com/heisenyu/hanime-server
- **本仓库地址**: https://github.com/PatchouriNya/hanime-server
- **维护者联系邮箱**: 609206398@qq.com
- **维护承诺**: 如果原作者停止维护，本仓库将继续提供更新和修复

### ✅ 更新内容

以下是对原项目的主要更新和修复：

1. **大幅优化内存占用**: 
   - 使用 Alpine 基础镜像替代 Ubuntu，镜像体积大幅减小
   - 完全移除 DrissionPage（依赖 Chromium），改用 BeautifulSoup + lxml 进行页面解析
   - 使用 zhconv 替代 opencc，解决 Alpine 兼容性问题
   - 内存占用从 >1GB 降至约 65MB，适合 NAS 等资源受限设备

2. **移除 CF Bypass 依赖**:
   - 重写 cloudflare_bypass.py，支持代理直连模式
   - 不再需要额外的 CF 绕过服务容器
   - 简化部署配置，只需一个容器即可运行

3. **修复页面404问题**: 
   - 修改 nginx.conf，将 `server_name localhost` 改为 `_` 并添加 `default_server`
   - 删除 Dockerfile 中默认站点配置
   - 修改 start.sh，使用直接运行 nginx 命令代替 `service nginx start`

4. **修复页面内容解析问题**:
   - 更新 video_service.py 中的视频解析选择器，适配新的页面结构
   - 使用 BeautifulSoup 替代 DrissionPage 进行 HTML 解析
   - 修复分类列表中 videos 字段为空的问题

5. **新增用户账户功能**:
   - 创建收藏系统（喜欢的影片）
   - 创建稍后观看列表
   - 创建播放清单功能
   - 创建观看历史记录
   - 使用 SQLite 数据库持久化存储

6. **新增设置页面**:
   - 代理设置（运行时生效）
   - 代理测试功能（验证代理是否可用）
   - 数据导入/导出功能
   - 数据清空功能

7. **优化部署配置**:
   - 添加 GitHub Actions 自动构建多平台镜像（amd64 + arm64）
   - 创建 NAS 专用 docker-compose.nas.yml
   - 添加 .gitignore 和 .dockerignore 配置
   - 修复 ARM64 架构适配问题

8. **修复后端启动问题**:
   - 修复 UserService 初始化时事件循环未启动导致的 RuntimeError
   - 将数据库初始化移到 FastAPI lifespan 事件中

---

## <span id="-功能特色">✨ 功能特色</span>

<div align="center">
  <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-bottom: 30px;">
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🎬</div>
      <div><b>视频浏览</b></div>
      <div style="font-size: 14px;">首页推荐、分类浏览</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🔍</div>
      <div><b>高级搜索</b></div>
      <div style="font-size: 14px;">多条件组合查询</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🌙</div>
      <div><b>暗黑模式切换</b></div>
      <div style="font-size: 14px;">支持明暗主题切换</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">📥</div>
      <div><b>下载管理</b></div>
      <div style="font-size: 14px;">批量下载与管理</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">❤️</div>
      <div><b>收藏管理</b></div>
      <div style="font-size: 14px;">喜欢的影片收藏</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">⏱️</div>
      <div><b>稍后观看</b></div>
      <div style="font-size: 14px;">视频收藏列表</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">📋</div>
      <div><b>播放清单</b></div>
      <div style="font-size: 14px;">自定义视频清单</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">📜</div>
      <div><b>观看历史</b></div>
      <div style="font-size: 14px;">记录观看进度</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">⚙️</div>
      <div><b>设置页面</b></div>
      <div style="font-size: 14px;">代理配置、数据管理</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🔒</div>
      <div><b>用户登录系统</b></div>
      <div style="font-size: 14px;">JWT认证、路由保护</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🔍</div>
      <div><b>敏感图片屏蔽</b></div>
      <div style="font-size: 14px;">毛玻璃打码模式</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">📱</div>
      <div><b>响应式设计</b></div>
      <div style="font-size: 14px;">适配多种设备</div>
    </div>
    <div style="text-align: center; width: 200px;">
      <div style="font-size: 32px;">🖥️</div>
      <div><b>NAS 部署</b></div>
      <div style="font-size: 14px;">家庭媒体中心</div>
    </div>
  </div>
</div>

## <span id="-项目截图">📷 项目截图</span>

<table border="0" width="100%">
  <tr>
    <td width="50%" align="center">
      <img src="img/主页.png" alt="主页" width="100%" style="border-radius: 8px;">
      <br><b>主页</b><br>展示推荐内容和分类
    </td>
    <td width="50%" align="center">
      <img src="img/视频详情页.png" alt="视频详情页" width="100%" style="border-radius: 8px;">
      <br><b>视频详情页</b><br>播放器和相关信息
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="img/搜索页.png" alt="搜索页" width="100%" style="border-radius: 8px;">
      <br><b>搜索页</b><br>快速找到想要的内容
    </td>
    <td width="50%" align="center">
      <img src="img/高级搜索.png" alt="高级搜索" width="100%" style="border-radius: 8px;">
      <br><b>高级搜索</b><br>多条件筛选
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="img/下载页.png" alt="下载页" width="100%" style="border-radius: 8px;">
      <br><b>下载页</b><br>管理下载任务
    </td>
    <td width="50%" align="center">
      <img src="img/手机端下载页示例.png" alt="手机端下载页示例" width="50%" style="border-radius: 8px;">
      <br><b>手机端适配</b><br>移动设备完美支持
    </td>
  </tr>
</table>

## <span id="️-技术架构">🛠️ 技术架构</span>

<div align="center">
  <table>
    <tr>
      <th>后端技术</th>
      <th>前端技术</th>
    </tr>
    <tr>
      <td>
        <ul>
          <li>Python 3.10</li>
          <li>FastAPI 框架</li>
          <li>SQLite 数据存储</li>
          <li>异步下载服务</li>
          <li>视频元数据服务</li>
          <li>Cloudflare 绕过实现</li>
          <li>LRU缓存优化</li>
          <li>用户账户服务</li>
        </ul>
      </td>
      <td>
        <ul>
          <li>Vue.js 框架</li>
          <li>TypeScript 类型支持</li>
          <li>Vite 构建工具</li>
          <li>Vue Router 路由管理</li>
          <li>Pinia 状态管理</li>
          <li>Plyr 视频播放器组件</li>
          <li>Element Plus UI组件</li>
          <li>响应式布局设计</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

### 核心组件

- **下载服务**: 管理视频下载队列、状态跟踪和错误处理
- **视频服务**: 提供视频搜索、元数据解析和内容推荐
- **用户服务**: 管理收藏、稍后观看、播放清单、观看历史
- **数据缓存**: 优化性能和减少网络请求
- **代理支持**: 内置代理支持，可通过代理直连目标网站
- **Plyr播放器**: 提供流畅的视频播放体验

## <span id="-部署指南">🚀 部署指南</span>

### Docker Compose 一键部署（推荐）

本项目支持通过 GitHub Actions 自动构建多平台镜像（amd64 + arm64），可直接在 NAS 上一键部署。

#### 方式一：使用已构建的镜像（推荐）

1. 创建 `docker-compose.yml` 文件：

```yaml
services:
  hanime-server:
    image: ghcr.io/patchourinya/hanime-server:latest
    container_name: hanime-server
    ports:
      - "7788:7788"
    volumes:
      # 挂载一个目录即可持久化所有用户数据（数据库、下载文件、封面）
      - /volume1/docker/hanime/data:/app/backend/data
    environment:
      - TZ=Asia/Shanghai
      - USE_PROXY=false
      - PROXY_URL=
    restart: unless-stopped
```

2. 运行容器：

```bash
# 创建数据目录
mkdir -p /volume1/docker/hanime/data

# 启动容器
docker-compose up -d
```

3. 访问应用：
   - 前端界面：http://你的NASIP:7788

4. **登录系统**（v2.0.0+）：
   - 默认用户名：`admin`
   - 默认密码：`666666`
   - 暂不开放注册功能
   - 未登录用户无法访问任何路由

#### 方式二：使用项目自带的 docker-compose.nas.yml

```bash
# 创建数据目录
mkdir -p /volume1/docker/hanime/data

# 拉取镜像并启动
docker-compose -f docker-compose.nas.yml pull
docker-compose -f docker-compose.nas.yml up -d
```

### 代理配置

如果需要使用代理访问目标网站，可以通过以下方式配置：

#### 方式一：环境变量配置（启动时）

```yaml
environment:
  - USE_PROXY=true
  - PROXY_URL=http://你的代理地址:端口
```

#### 方式二：设置页面配置（运行时）

1. 进入设置页面
2. 开启代理并填写代理地址（如 `http://192.168.1.xxx:7890`）
3. 点击"保存设置"
4. 点击"测试代理"验证代理是否生效

### 内存优化

本项目经过深度优化，内存占用极低：

- **使用 Alpine 基础镜像**：镜像体积小，运行时资源消耗少
- **移除 Chromium 依赖**：不再使用 DrissionPage，改用 BeautifulSoup 解析
- **内存占用**：约 65MB（相比原项目 >1GB 大幅降低）

### NAS 部署指南

本项目适合在各类NAS系统上部署：

#### 绿联 (UGreen) NAS 部署（以 4800Plus 为例）
1. 在应用中心安装 Docker
2. 创建部署目录：`mkdir -p /volume1/docker/hanime/data`
3. 创建或下载 docker-compose.nas.yml
4. 运行 `docker-compose -f docker-compose.nas.yml up -d`
5. 访问：http://你的NASIP:7788

#### 群晖 (Synology) NAS 部署
1. 在套件中心安装Docker
2. 在Docker应用中创建上述docker-compose.yml文件
3. 映射下载目录到您的媒体文件夹
4. 运行容器

#### 威联通 (QNAP) NAS 部署
1. 通过Container Station安装
2. 使用上述docker-compose配置
3. 映射存储卷到媒体文件夹

#### 其他 NAS 系统
只要支持Docker，均可按照类似步骤进行部署

### 定制构建

如果您希望自行构建 Docker 镜像：

```bash
# 克隆仓库
git clone https://github.com/你的用户名/hanime-server
cd hanime-server

# 构建镜像
docker-compose build --no-cache

# 运行容器
docker-compose up -d
```

### 手动部署

#### 后端部署
1. 进入 backend 目录
2. 安装依赖：`pip install -r requirements.txt`
3. 运行服务器：`python main.py`

通过 http://localhost:8000/docs 访问 API 文档

#### 前端部署
1. 进入 frontend 目录
2. 安装依赖：`npm install`
3. 开发模式：`npm run dev`
4. 构建生产版：`npm run build`

通过 http://localhost:7788 访问前端页面

## <span id="-免责声明">⚠️ 免责声明</span>

本应用程序（以下简称"本应用"）与原站点及其关联方无任何隶属、合作或授权关系，特此声明如下：

### 🔍 数据来源

本应用通过合法技术手段仅获取目标网站公开显示的信息，不涉及：

* 🔒 用户账户等隐私数据
* 🛑 网站后端数据库访问
* ⚠️ 任何形式的注入攻击

### ⚖️ 使用限制

本应用提供的所有内容仅用于：

* 📚 技术研究学习
* ✨ 用户体验优化
* 🚫 非商业用途展示

### ©️ 版权归属

原始视频/图文内容版权均归原始网站或内容制作/发行方所有，本应用:

* 💾 不存储任何版权内容（除用户主动下载）
* ✂️ 不修改原始内容
* 🏷️ 不声称拥有内容所有权

### 🛡️ 责任豁免

使用者应知晓：

* ⏳ 本应用不保证数据的完整性和实时性
* 🙅‍♂️ 使用产生的一切后果由用户自行承担
* ⛔ 不得用于非法用途

## <span id="-许可证">📄 许可证</span>

本项目采用 Apache License Version 2.0 许可证，详细条款请参阅项目根目录下的 LICENSE 文件。

主要条款包括：
- 允许商用、修改、分发和私有使用
- 要求保留版权声明和许可证文件
- 提供修改说明（如有）
- 不提供质量担保
- 不承担用户使用风险

---

## 📧 联系方式

- **维护者**: 本仓库维护者
- **联系邮箱**: 609206398@qq.com

如果原作者停止维护，本仓库将继续提供更新和修复。

---

<div align="center">
  <p>ℹ️ 温馨提示：建议通过官方渠道支持原站内容，并点击广告以支持网站运营者。</p>
  <p>🌟 如果您喜欢这个项目，请考虑给它点个星！</p>
</div>
