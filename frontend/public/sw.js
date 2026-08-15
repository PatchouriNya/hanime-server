/* Hanime Server Service Worker (v4.0.0 PWA)
 *
 * 策略：
 * - 预缓存应用外壳（index.html + 图标）
 * - 导航请求（页面跳转）：网络优先，失败回退缓存（保证离线可打开上次会话的页面壳）
 * - /assets/ 静态资源（Vite 产物带内容 hash）：缓存优先（长缓存安全）
 * - /api/ 请求：永不缓存（始终走网络，保证数据实时性）
 */
const CACHE_NAME = 'hanime-app-v1';
const APP_SHELL = [
  '/',
  '/index.html',
  '/logo.png',
  '/pwa-192.png',
  '/pwa-512.png',
  '/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // 只处理同源请求
  if (url.origin !== self.location.origin) return;

  // API 请求：始终走网络
  if (url.pathname.startsWith('/api/')) return;

  // 静态资源（Vite hash 产物）：缓存优先
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        });
      })
    );
    return;
  }

  // 页面导航：网络优先，失败回退缓存
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('/index.html', copy));
          return response;
        })
        .catch(() => caches.match('/index.html'))
    );
    return;
  }

  // 其他（manifest、图标等）：缓存优先 + 网络回填
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        return response;
      });
    })
  );
});
