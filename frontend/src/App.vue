<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import AppHeader from "./components/AppHeader.vue";
import AppSidebar from "./components/AppSidebar.vue";
import './assets/styles/common.css';
import './assets/styles/animations.css';
import { useDownloadStore } from './stores/download';
import { useRouter } from 'vue-router';
import request from './utils/request';

const sidebarOpen = ref(false);
const theme = ref(localStorage.getItem('theme') || 'dark');
const downloadStore = useDownloadStore();
const router = useRouter();

// 切换侧边栏
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

// 关闭侧边栏
const closeSidebar = () => {
  sidebarOpen.value = false;
};

// 保存主题到后端
const saveThemeToServer = async (themeValue: string) => {
  try {
    if (localStorage.getItem('token')) {
      await request.post('/accounts/me/settings', { theme: themeValue });
    }
  } catch (e) {
    // 静默失败
  }
};

// 从后端加载主题
const loadThemeFromServer = async () => {
  try {
    if (localStorage.getItem('token')) {
      const response = await request.get('/accounts/me/settings');
      if (response.data?.settings?.theme) {
        theme.value = response.data.settings.theme;
        localStorage.setItem('theme', theme.value);
      }
    }
  } catch (e) {
    // 静默失败
  }
};

// 切换主题
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', theme.value);
  setTheme();
  saveThemeToServer(theme.value);
};

// 登出
const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('tokenType');
  localStorage.removeItem('username');
  localStorage.removeItem('loginTime');
  router.push('/login');
};

// 应用主题到 HTML 元素
const setTheme = () => {
  const htmlEl = document.documentElement;
  if (theme.value === 'dark') {
    htmlEl.classList.add('dark');
    htmlEl.classList.remove('light');
  } else {
    htmlEl.classList.add('light');
    htmlEl.classList.remove('dark');
  }
};

// 监听主题变化
watch(theme, () => {
  setTheme();
});

// 侧边栏打开时锁定body滚动
watch(sidebarOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : '';
});

// 组件挂载时设置主题
onMounted(async () => {
  // 从后端加载用户主题设置
  await loadThemeFromServer();

  // 确保默认使用暗黑模式
  if (!localStorage.getItem('theme')) {
    localStorage.setItem('theme', 'dark');
    theme.value = 'dark';
  }
  setTheme();

  // 仅已登录时初始化下载存储和WebSocket连接
  if (localStorage.getItem('token')) {
    downloadStore.initializeDownloads();
  }

  // 监听登录事件，登录后刷新主题
  window.addEventListener('user-login', async () => {
    await loadThemeFromServer();
    setTheme();
  });
});
</script>

<template>
  <div class="app">
    <AppHeader 
      :sidebar-open="sidebarOpen"
      :current-theme="theme"
      @toggle-sidebar="toggleSidebar"
      @toggle-theme="toggleTheme"
    />
    
    <AppSidebar 
      :is-open="sidebarOpen"
      @close="closeSidebar"
      @toggle-theme="toggleTheme"
      @logout="handleLogout"
    />
    
    <main class="app-content">
      <transition name="page" mode="out-in">
        <router-view :key="$route.fullPath" />
      </transition>
    </main>

    <footer class="app-footer">
      <div class="container">
        <p>&copy; {{ new Date().getFullYear() }} Hanime View. 仅供学习研究使用。</p>
      </div>
    </footer>
  </div>
</template>

<style>
/* 基础样式设置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Roboto', sans-serif;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-color);
}

.app-content {
  flex: 1;
  margin-top: 10px;
}

.app-footer {
  background-color: var(--bg-secondary-color);
  border-top: 1px solid var(--border-color);
  padding: 20px 0;
  margin-top: 30px;
  text-align: center;
  color: var(--text-secondary-color);
  font-size: 14px;
}

/* Element Plus 图标全局样式 */
.el-icon {
  vertical-align: middle;
}

/* 路由切换动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.page-enter-active {
  transition-delay: 50ms;
}

/* 页面加载骨架屏 */
.skeleton-loader {
  background: linear-gradient(90deg, var(--bg-secondary-color) 25%, var(--hover-bg-color) 50%, var(--bg-secondary-color) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
