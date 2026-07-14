# 修改记录

本文档记录了对原项目 [heisenyu/hanime-server](https://github.com/heisenyu/hanime-server) 的所有修改内容。

## 修改原因

1. **原项目兼容性问题**: 原项目使用 DrissionPage 依赖 Chromium，在 Alpine Docker 环境下无法正常运行
2. **内存占用过高**: DrissionPage + Chromium 组合导致内存占用超过 1GB，不适合 NAS 部署
3. **代理配置不便**: 需要运行时可切换代理设置
4. **缺少用户功能**: 没有收藏、观看历史等用户功能

## 修改内容

### 1. Dockerfile 修改

**文件**: `Dockerfile`

- 将基础镜像从 `python:3.10-slim` 改为 `python:3.10-alpine`，减小镜像体积
- 移除 DrissionPage 相关依赖安装
- 调整 Nginx 配置文件路径从 `/etc/nginx/conf.d/default.conf` 改为 `/etc/nginx/http.d/default.conf`（Alpine 系统路径）
- 添加 `PYTHONOPTIMIZE=2` 和 `PYTHONDONTWRITEBYTECODE=1` 环境变量

### 2. 依赖更新

**文件**: `backend/requirements.txt`

- 删除 `drissionpage~=4.1.0.17`（移除 Chromium 依赖，大幅减少内存占用）
- 添加 `bs4~=0.0.2`（BeautifulSoup HTML 解析）
- 添加 `lxml~=5.3.0`（XML/HTML 解析器）
- 添加 `zhconv~=1.4.1`（简繁体转换，替代 opencc）

### 3. 核心服务重写

**文件**: `backend/app/services/video_service.py`

- 将 `from DrissionPage.common import make_session_ele` 替换为 `from bs4 import BeautifulSoup`
- 将所有 `page_ele.ele()` 和 `page_ele.eles()` 方法替换为 BeautifulSoup 的 `find()` 和 `find_all()`
- 将 `attr()` 替换为 `get()`
- 将 `text` 属性替换为 `get_text(strip=True)`
- 将 XPath 选择器转换为 CSS 选择器或 BeautifulSoup API

### 4. 简繁体转换工具

**文件**: `backend/app/utils/chinese_converter.py`

- 将 `import opencc` 替换为 `from zhconv import convert`
- 使用 `convert(text, 'zh-hans')` 替代 `opencc.OpenCC('t2s.json').convert(text)`
- 使用 `convert(text, 'zh-hant')` 替代 `opencc.OpenCC('s2t.json').convert(text)`

### 5. Cloudflare 绕过优化

**文件**: `backend/app/utils/cloudflare_bypass.py`

- 移除 DrissionPage 模式，仅保留 HTTP 代理直连和 bypass 服务模式
- 添加降级机制：bypass 服务不可用时自动使用代理直连

### 6. 启动脚本修改

**文件**: `start.sh`

- 将 `#!/bin/bash` 改为 `#!/bin/sh` 以适配 Alpine 系统
- 使用直接运行 nginx 命令代替 `service nginx start`

### 7. Nginx 配置优化

**文件**: `frontend/nginx.conf`

- 修改 `server_name` 为 `_` 并添加 `default_server`
- 确保配置格式符合 Alpine 系统要求

### 8. 容器资源限制

**文件**: `docker-compose.yml` 和 `docker-compose.nas.yml`

- 添加内存限制：512MB
- 添加 CPU 限制：0.5 核
- 添加内存预留：256MB
- 添加 CPU 预留：0.25 核
- 添加 `PYTHONOPTIMIZE=2` 和 `PYTHONDONTWRITEBYTECODE=1` 环境变量

### 9. GitHub Actions 配置

**文件**: `.github/workflows/docker-build.yml`

- 添加多平台镜像构建（amd64 + arm64）
- 配置 GHCR 镜像推送

### 10. 前端设置页面

**文件**: `frontend/src/views/Settings.vue`

- 添加代理开关和代理地址配置
- 添加代理测试功能
- 添加数据导入/导出功能

### 11. 用户功能

**文件**: `backend/app/services/user_service.py`, `backend/app/api/endpoints/accounts.py`

- 添加收藏系统
- 添加稍后观看列表
- 添加播放清单功能
- 添加观看历史记录

## 内存优化效果

| 优化项 | 优化前 | 优化后 |
|--------|--------|--------|
| 基础镜像 | python:3.10-slim (~200MB) | python:3.10-alpine (~50MB) |
| 浏览器依赖 | DrissionPage + Chromium (~500MB+) | BeautifulSoup + lxml (~20MB) |
| 容器内存限制 | 无限制（>1GB） | 512MB |
| 简繁转换 | opencc (C 扩展) | zhconv (纯 Python) |

## 部署配置

### 推荐环境变量

```bash
USE_PROXY=true              # 是否启用代理
PROXY_URL=http://xxx:7890   # 代理地址
TZ=Asia/Shanghai            # 时区
PYTHONOPTIMIZE=2            # Python 代码优化
PYTHONDONTWRITEBYTECODE=1   # 不生成 .pyc 文件
```

### 资源限制推荐

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

## 维护者信息

- **原项目**: https://github.com/heisenyu/hanime-server
- **本仓库**: https://github.com/PatchouriNya/hanime-server
- **联系邮箱**: 609206398@qq.com
- **维护承诺**: 如果原作者停止维护，本仓库将继续提供更新和修复