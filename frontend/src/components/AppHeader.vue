<template>
  <header class="app-header">
    <div class="header-left">
      <button class="menu-button" @click="toggleSidebar">
        <el-icon :size="24"><Menu /></el-icon>
      </button>
      <button v-if="showBackButton" class="back-button" @click="goBack">
        <el-icon :size="24"><Back /></el-icon>
      </button>
      <div class="title-wrapper">
        <h1 class="app-title" @click="goToHome">HanimeViewer</h1>
        <span class="version-badge">v2.1.3</span>
      </div>
    </div>
    <div class="header-right">
      <button class="theme-button" @click="toggleTheme">
        <el-icon :size="24">
          <Moon v-if="currentTheme === 'light'" />
          <Sunny v-else />
        </el-icon>
      </button>
      <button class="calendar-button" @click="goToCalendar">
        <el-icon :size="24"><Calendar /></el-icon>
      </button>
      <button class="search-button" @click="goToSearch">
        <el-icon :size="24"><Search /></el-icon>
      </button>
      <button class="changelog-button" @click="goToChangelog">
        <el-icon :size="24"><Document /></el-icon>
      </button>
    </div>
  </header>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Menu, Back, Calendar, Search, Moon, Sunny, Document } from '@element-plus/icons-vue';
import { mitt } from '../utils/mitt';

export default defineComponent({
  name: 'AppHeader',
  components: {
    Menu,
    Back,
    Calendar,
    Search,
    Moon,
    Sunny,
    Document
  },
  props: {
    sidebarOpen: {
      type: Boolean,
      default: false
    },
    currentTheme: {
      type: String,
      default: 'dark'
    }
  },
  emits: ['toggle-sidebar', 'toggle-theme'],
  setup(props, { emit }) {
    const router = useRouter();
    const route = useRoute();

    const showBackButton = computed(() => {
      return route.path !== '/';
    });

    const toggleSidebar = () => {
      emit('toggle-sidebar');
    };

    const toggleTheme = () => {
      emit('toggle-theme');
    };

    const goBack = () => {
      router.back();
    };

    const goToHome = () => {
      if (route.path === '/') {
        // 已在首页，触发刷新推荐
        mitt.emit('refresh-home');
      } else {
        router.push('/');
      }
    };

    const goToCalendar = () => {
      router.push('/calendar');
    };

    const goToSearch = () => {
      router.push('/search');
    };

    const goToChangelog = () => {
      router.push('/changelog');
    };

    return {
      showBackButton,
      toggleSidebar,
      toggleTheme,
      goBack,
      goToHome,
      goToCalendar,
      goToSearch,
      goToChangelog
    };
  }
});
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: var(--bg-color);
  color: var(--text-color);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--bg-secondary-color);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-button, .back-button, .calendar-button, .search-button, .theme-button, .changelog-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.menu-button:hover, .back-button:hover, .calendar-button:hover, .search-button:hover, .theme-button:hover, .changelog-button:hover {
  background-color: var(--hover-bg-color);
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.app-title {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color);
}

.version-badge {
  font-size: 11px;
  padding: 2px 6px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.title-wrapper:hover .version-badge {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

.header-right {
  margin-left: auto;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link {
  text-decoration: none;
  color: var(--text-color);
  cursor: pointer;
}

@media (max-width: 480px) {
  .app-title {
    font-size: 20px;
  }
}
</style> 