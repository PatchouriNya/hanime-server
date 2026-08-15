# ==================== 前端构建阶段 ====================
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

RUN npm config set registry https://registry.npmmirror.com

# 依赖层：只复制锁文件，package.json / lock 不变则此层缓存复用
COPY frontend/package*.json ./
RUN npm ci || npm install
# 源码层：业务代码改动不影响上面的依赖缓存
COPY frontend/ ./
RUN npx vite build && rm -rf node_modules .git

# ==================== 后端运行阶段 ====================
FROM python:3.10-alpine

LABEL org.opencontainers.image.source=https://github.com/PatchouriNya/hanime-server
LABEL org.opencontainers.image.description="Hanime Server - A self-hosted anime video server"
LABEL org.opencontainers.image.licenses=MIT

ENV TZ=Asia/Shanghai \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN set -ex && \
    apk update && \
    apk add --no-cache nginx curl ffmpeg && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# 依赖层：先只复制 requirements.txt 并安装依赖，
# 后端代码改动不再触发依赖重装（Docker 层缓存复用的关键）
COPY backend/requirements.txt /app/backend/requirements.txt
WORKDIR /app/backend

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    find /usr/local/lib -type f -name "*.pyc" -delete && \
    find /usr/local/lib -type d -name "__pycache__" -delete && \
    rm -rf /root/.cache

# 源码层：业务代码复制到依赖之上
COPY backend/ /app/backend/

COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/http.d/default.conf

RUN if [ ! -f /usr/share/nginx/html/index.html ]; then echo "ERROR: Frontend build output missing!" && exit 1; fi

COPY start.sh /app/
RUN chmod +x /app/start.sh

EXPOSE 7788

CMD ["/app/start.sh"]
