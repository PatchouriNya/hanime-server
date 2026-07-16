<template>
  <div class="sidebar-container" :class="{ 'open': isOpen }">
    <div class="sidebar-overlay" @click="closeSidebar"></div>
    <aside class="sidebar">
      <div class="user-info" @click="showAvatarPicker = true">
        <div class="avatar" :class="{ 'has-avatar': avatarUrl }">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" :class="{ 'blurred': shouldBlur && blurMode === 'blur' }" alt="avatar" />
          <div v-if="avatarUrl && shouldBlur && blurMode === 'blur'" class="avatar-blur-overlay"></div>
          <div v-if="avatarUrl && shouldBlur && blurMode === 'hide'" class="avatar-hide-overlay"></div>
          <span v-if="!avatarUrl" class="avatar-text">{{ avatarLetter }}</span>
        </div>
        <div class="user-details">
          <div class="username">{{ currentUsername || '未登录' }}</div>
          <div class="login-hint" v-if="currentUsername">点击更换头像</div>
        </div>
      </div>
      
      <nav class="nav-menu">
        <router-link to="/" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><HomeFilled /></el-icon> 主页
        </router-link>
        <router-link to="/settings" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><Setting /></el-icon> 设置
        </router-link>
        <div class="nav-item" @click="toggleTheme">
          <el-icon :size="20">
            <component :is="currentTheme === 'dark' ? 'Sunny' : 'Moon'" />
          </el-icon>
          {{ currentTheme === 'dark' ? '浅色模式' : '深色模式' }}
        </div>
      </nav>
      
      <div class="divider"></div>
      
      <nav class="nav-menu">
        <div class="menu-title">我的清单</div>
        <router-link to="/watch-later" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><Timer /></el-icon> 稍后观看
        </router-link>
        <router-link to="/favorites" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><Star /></el-icon> 喜欢的影片
        </router-link>
        <router-link to="/playlists" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><Film /></el-icon> 播放清单
        </router-link>
      </nav>
      
      <div class="divider"></div>
      
      <nav class="nav-menu">
        <div class="menu-title">影片</div>
        <router-link to="/history" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><VideoCamera /></el-icon> 观看历史
        </router-link>
        <router-link to="/downloads" class="nav-item" @click="closeSidebar">
          <el-icon :size="20"><Download /></el-icon> 下载
        </router-link>
      </nav>

      <div class="sidebar-spacer"></div>
      
      <div class="divider"></div>
      
      <div class="nav-menu logout-section">
        <div class="nav-item logout-btn" @click="handleLogout">
          <el-icon :size="20"><SwitchButton /></el-icon> 退出登录
        </div>
      </div>
    </aside>

    <!-- 头像选择弹窗 -->
    <el-dialog
      v-model="showAvatarPicker"
      title="选择头像"
      :width="isMobile ? '90%' : '520px'"
      :close-on-click-modal="true"
      class="avatar-picker-dialog"
    >
      <div v-if="downloadedCovers.length === 0" class="empty-covers">
        <el-icon :size="48"><Picture /></el-icon>
        <p>暂无已下载的番剧，下载番剧后可使用其封面作为头像</p>
      </div>
      <div v-else class="cover-grid">
        <div 
          v-for="item in downloadedCovers" 
          :key="item.video_id"
          class="cover-item"
          :class="{ 'selected': selectedCoverId === item.video_id }"
          @click="selectedCoverId = item.video_id"
        >
          <img
            :src="`/api/downloads/cover/${item.video_id}?token=${authToken}`"
            :alt="item.title"
            class="cover-img"
            loading="lazy"
            @error="onCoverError($event)"
          />
          <div class="cover-title" :title="item.title">{{ item.title }}</div>
          <div v-if="selectedCoverId === item.video_id" class="selected-mark">
            <el-icon :size="18"><Check /></el-icon>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAvatarPicker = false">取消</el-button>
        <el-button @click="resetAvatar" type="warning">恢复默认</el-button>
        <el-button @click="confirmAvatar" type="primary" :disabled="!selectedCoverId && avatarUrl">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useContentSettings } from '../composables/useContentSettings';
import { 
  HomeFilled, 
  Setting, 
  Moon, 
  Sunny, 
  Timer, 
  Star, 
  Film, 
  VideoCamera, 
  Download,
  SwitchButton,
  Picture,
  Check
} from '@element-plus/icons-vue';

interface DownloadedCover {
  video_id: string;
  title: string;
}

export default defineComponent({
  name: 'AppSidebar',
  components: {
    HomeFilled,
    Setting,
    Moon,
    Sunny,
    Timer,
    Star,
    Film,
    VideoCamera,
    Download,
    SwitchButton,
    Picture,
    Check
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'toggle-theme', 'logout'],
  setup(props, { emit }) {
    const router = useRouter();
    const { shouldBlur, mode: blurMode } = useContentSettings();
    const currentTheme = ref(localStorage.getItem('theme') || 'dark');
    const showAvatarPicker = ref(false);
    const downloadedCovers = ref<DownloadedCover[]>([]);
    const selectedCoverId = ref<string>('');
    const avatarUrl = ref('');
    const authToken = ref(localStorage.getItem('token') || '');
    const isMobile = ref(window.innerWidth <= 480);

    window.addEventListener('resize', () => {
      isMobile.value = window.innerWidth <= 480;
    });

    const currentUsername = ref(localStorage.getItem('username') || '');
    const avatarLetter = computed(() => {
      return currentUsername.value ? currentUsername.value.charAt(0).toUpperCase() : '?';
    });

    // 获取当前主题
    const updateCurrentTheme = () => {
      currentTheme.value = localStorage.getItem('theme') || 'dark';
    };

    // 加载已下载封面列表
    const loadDownloadedCovers = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch('/api/downloads/history', {
          headers: { 'Authorization': `bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          downloadedCovers.value = data
            .filter((item: any) => item.status === 'completed')
            .map((item: any) => ({
              video_id: item.video_id,
              title: item.title || item.video_id
            }));
        }
      } catch (e) {
        console.error('加载下载封面失败:', e);
      }
    };

    // 加载用户头像设置
    const loadAvatar = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch('/api/accounts/me/settings', {
          headers: { 'Authorization': `bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          if (data.settings && data.settings.avatar_video_id) {
            avatarUrl.value = `/api/downloads/cover/${data.settings.avatar_video_id}?token=${token}`;
          } else {
            avatarUrl.value = '';
          }
        }
      } catch (e) {
        console.error('加载头像设置失败:', e);
      }
    };

    // 保存用户头像设置
    const saveAvatar = async (videoId: string | null) => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        // 获取当前设置
        const getRes = await fetch('/api/accounts/me/settings', {
          headers: { 'Authorization': `bearer ${token}` }
        });
        let currentSettings: any = {};
        if (getRes.ok) {
          const data = await getRes.json();
          currentSettings = data.settings || {};
        }
        
        if (videoId) {
          currentSettings.avatar_video_id = videoId;
        } else {
          delete currentSettings.avatar_video_id;
        }
        
        await fetch('/api/accounts/me/settings', {
          method: 'POST',
          headers: {
            'Authorization': `bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(currentSettings)
        });
      } catch (e) {
        console.error('保存头像设置失败:', e);
      }
    };

    const confirmAvatar = async () => {
      if (selectedCoverId.value) {
        await saveAvatar(selectedCoverId.value);
        avatarUrl.value = `/api/downloads/cover/${selectedCoverId.value}?token=${localStorage.getItem('token')}`;
        showAvatarPicker.value = false;
        ElMessage.success('头像已更新');
      }
    };

    const resetAvatar = async () => {
      await saveAvatar(null);
      avatarUrl.value = '';
      selectedCoverId.value = '';
      showAvatarPicker.value = false;
      ElMessage.success('已恢复默认头像');
    };

    const handleLogout = async () => {
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });
        emit('logout');
        closeSidebar();
      } catch {
        // 用户取消
      }
    };

    const closeSidebar = () => {
      emit('close');
    };
    
    const toggleTheme = () => {
      emit('toggle-theme');
      setTimeout(updateCurrentTheme, 100);
    };

    const onCoverError = (e: Event) => {
      const img = e.target as HTMLImageElement;
      img.style.display = 'none';
    };

    watch(showAvatarPicker, (val) => {
      if (val) {
        loadDownloadedCovers();
        selectedCoverId.value = '';
      }
    });

    const refreshUsername = () => {
      currentUsername.value = localStorage.getItem('username') || '';
    };

    onMounted(() => {
      loadAvatar();
      refreshUsername();
      // 监听 storage 事件（跨标签页同步）和自定义事件（同标签页登录）
      window.addEventListener('storage', refreshUsername);
      window.addEventListener('user-login', refreshUsername);
    });

    return {
      currentTheme,
      currentUsername,
      avatarLetter,
      avatarUrl,
      authToken,
      shouldBlur,
      blurMode,
      showAvatarPicker,
      downloadedCovers,
      selectedCoverId,
      closeSidebar,
      toggleTheme,
      handleLogout,
      confirmAvatar,
      resetAvatar,
      onCoverError,
      isMobile
    };
  }
});
</script>

<style scoped>
.sidebar-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  pointer-events: none;
}

.sidebar-container.open {
  pointer-events: auto;
}

.sidebar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  backdrop-filter: blur(0px);
}

.sidebar-container.open .sidebar-overlay {
  opacity: 1;
  pointer-events: auto;
  backdrop-filter: blur(4px);
}

.sidebar {
  position: absolute;
  top: 0;
  left: -280px;
  width: 280px;
  height: 100%;
  background-color: var(--bg-secondary-color);
  transition: left 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 20px 0 12px;
  box-shadow: 8px 0 30px rgba(0, 0, 0, 0.3);
}

.sidebar-container.open .sidebar {
  left: 0;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: var(--hover-bg-color);
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-weight: bold;
  margin-right: 15px;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid transparent;
  transition: border-color 0.2s;
  position: relative;
}

.avatar.has-avatar {
  border-color: var(--primary-color);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-img.blurred {
  filter: blur(20px) brightness(0.8);
}

.avatar-blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  pointer-events: none;
}

.avatar-hide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary-color);
  font-size: 12px;
}

.avatar-text {
  font-size: 16px;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.username {
  color: var(--text-color);
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.login-hint {
  color: var(--text-secondary-color);
  font-size: 12px;
  margin-top: 2px;
}

.nav-menu {
  padding: 10px 0;
}

.menu-title {
  padding: 10px 20px;
  color: var(--text-secondary-color);
  font-size: 14px;
  text-transform: uppercase;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: var(--text-color);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
  background-color: var(--primary-color);
  transform: scaleY(0);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item:hover {
  background-color: var(--hover-bg-color);
  padding-left: 24px;
}

.nav-item:hover::before {
  transform: scaleY(1);
}

.nav-item .el-icon {
  margin-right: 15px;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item:hover .el-icon {
  transform: translateX(4px);
}

.divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 5px 0;
}

.sidebar-spacer {
  flex: 1;
}

.logout-section {
  padding-bottom: 0;
}

.logout-btn {
  color: #f56c6c !important;
}

.logout-btn:hover {
  background-color: rgba(245, 108, 108, 0.1) !important;
}

.logout-btn::before {
  background-color: #f56c6c !important;
}

/* 头像选择弹窗 */
.cover-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.cover-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.2s;
  background-color: var(--bg-color);
}

.cover-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.cover-item.selected {
  border-color: var(--primary-color);
}

.cover-img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}

.cover-title {
  padding: 6px 8px;
  font-size: 12px;
  color: var(--text-secondary-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-mark {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-covers {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary-color);
}

.empty-covers p {
  margin-top: 16px;
  font-size: 14px;
}

@media (max-width: 480px) {
  .cover-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    max-height: 300px;
  }

  .cover-title {
    padding: 4px 6px;
    font-size: 11px;
  }

  .selected-mark {
    width: 20px;
    height: 20px;
    top: 4px;
    right: 4px;
  }
}
</style>
