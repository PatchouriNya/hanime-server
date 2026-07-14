FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

RUN npm config set registry https://registry.npmmirror.com

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npx vite build && rm -rf node_modules .git

FROM python:3.10-alpine

ENV TZ=Asia/Shanghai \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN set -ex && \
    apk update && \
    apk add --no-cache nginx curl && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY backend/ /app/backend/
WORKDIR /app/backend

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib -type f -name "*.pyc" -delete && \
    find /usr/local/lib -type d -name "__pycache__" -delete && \
    rm -rf /root/.cache

COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/http.d/default.conf

RUN if [ ! -f /usr/share/nginx/html/index.html ]; then echo "ERROR: Frontend build output missing!" && exit 1; fi

COPY start.sh /app/
RUN chmod +x /app/start.sh

EXPOSE 7788

CMD ["/app/start.sh"]
