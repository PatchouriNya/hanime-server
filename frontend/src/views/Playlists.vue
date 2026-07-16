<template>
  <div class="playlists-page">
    <!-- 主视图：文件夹列表 -->
    <div v-if="!currentFolder" class="folders-view">
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <span class="title-accent"></span>
            播放清单
          </h1>
          <span class="folder-count" v-if="playlists.length > 0">{{ playlists.length }} 个文件夹</span>
        </div>
        <el-button type="primary" @click="showCreateDialog = true" class="create-btn">
          <el-icon :size="18"><FolderAdd /></el-icon> 新建文件夹
        </el-button>
      </div>

      <div v-if="loading" class="loading-container">
        <el-icon :size="36" class="loading-icon"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="playlists.length === 0" class="empty-container">
        <div class="empty-icon-wrapper">
          <el-icon :size="80" class="empty-icon"><FolderOpened /></el-icon>
        </div>
        <h3 class="empty-title">还没有播放清单</h3>
        <p class="empty-desc">创建你的第一个文件夹，开始整理影片</p>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon> 新建文件夹
        </el-button>
      </div>

      <div v-else class="folders-grid">
        <div
          v-for="playlist in playlists"
          :key="playlist.playlist_id"
          class="folder-card"
          @click="openFolder(playlist)"
        >
          <div class="folder-cover">
            <div v-if="playlist.videos.length > 0" class="cover-thumbs">
              <img
                v-for="(video, i) in playlist.videos.slice(0, 4)"
                :key="video.video_id"
                :src="video.cover_url"
                class="cover-thumb"
                :class="'thumb-' + (i + 1)"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <div class="cover-thumb-placeholder" v-for="i in (4 - Math.min(playlist.videos.length, 4))" :key="'ph-'+i"></div>
            </div>
            <div v-else class="cover-empty">
              <el-icon :size="36"><Folder /></el-icon>
            </div>
            <div class="folder-overlay"></div>
          </div>
          <div class="folder-info">
            <div class="folder-name-row">
              <h3 class="folder-name" :title="playlist.name">{{ playlist.name }}</h3>
              <div class="folder-menu" @click.stop>
                <el-dropdown trigger="click" placement="bottom-end">
                  <el-button class="menu-trigger" size="small" icon>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="startRename(playlist)">
                        <el-icon><Edit /></el-icon> 重命名
                      </el-dropdown-item>
                      <el-dropdown-item divided @click="handleDelete(playlist.playlist_id)">
                        <el-icon :color="'#f56c6c'"><Delete /></el-icon>
                        <span style="color: #f56c6c">删除</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            <p class="folder-meta">
              <el-icon :size="14"><VideoCamera /></el-icon>
              {{ playlist.videos.length }} 个影片
              <span class="meta-sep">·</span>
              {{ formatTime(playlist.updated_at) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 子视图：文件夹内部 -->
    <div v-else class="folder-detail-view">
      <div class="detail-header">
        <button class="back-btn" @click="currentFolder = null">
          <el-icon :size="20"><ArrowLeftBold /></el-icon>
        </button>
        <div class="detail-title-area">
          <template v-if="renamingId === currentFolder.playlist_id">
            <el-input
              v-model="renamingName"
              class="rename-input"
              size="large"
              @blur="confirmRename"
              @keyup.enter="confirmRename"
              ref="renameInputRef"
            />
          </template>
          <template v-else>
            <h2 class="detail-title">{{ currentFolder.name }}</h2>
            <button class="edit-name-btn" @click="startRename(currentFolder)">
              <el-icon :size="14"><Edit /></el-icon>
            </button>
          </template>
        </div>
        <el-button type="danger" plain size="small" @click="handleDelete(currentFolder.playlist_id)" class="delete-folder-btn">
          <el-icon><Delete /></el-icon> 删除文件夹
        </el-button>
      </div>

      <div v-if="currentFolder.videos.length === 0" class="folder-empty">
        <el-icon :size="64" class="empty-icon"><VideoCamera /></el-icon>
        <p>此文件夹暂无影片</p>
        <p class="folder-empty-hint">在影片详情页可将视频添加到播放清单</p>
      </div>

      <div v-else class="videos-grid">
        <div
          v-for="video in currentFolder.videos"
          :key="video.video_id"
          class="video-card"
          @click="handleVideoClick(video.video_id)"
        >
          <div class="video-cover">
            <img :src="video.cover_url" :alt="video.title" loading="lazy" referrerpolicy="no-referrer" />
            <div class="video-hover-actions">
              <el-button size="small" circle @click.stop="startMoveVideo(video.video_id)" title="移动到其他文件夹">
                <el-icon :size="14"><Switch /></el-icon>
              </el-button>
              <el-button size="small" circle type="danger" @click.stop="handleRemoveVideo(video.video_id)" title="移除此影片">
                <el-icon :size="14"><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <p class="video-title" :title="video.title">{{ video.title }}</p>
        </div>
      </div>
    </div>

    <!-- 新建文件夹弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建文件夹"
      :width="isMobile ? '90%' : '420px'"
      :close-on-click-modal="true"
    >
      <el-input
        v-model="newPlaylistName"
        placeholder="输入文件夹名称"
        class="create-input"
        @keyup.enter="handleCreate"
        ref="createInputRef"
      >
        <template #prefix>
          <el-icon><Folder /></el-icon>
        </template>
      </el-input>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :disabled="!newPlaylistName.trim()">创建</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认弹窗 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="删除文件夹"
      :width="isMobile ? '90%' : '420px'"
    >
      <div class="delete-warn">
        <el-icon :size="24" color="#f56c6c"><WarningFilled /></el-icon>
        <span>确定要删除此文件夹吗？文件夹内的影片也将被移除，此操作不可撤销。</span>
      </div>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>

    <!-- 移动影片弹窗 -->
    <el-dialog
      v-model="showMoveDialog"
      title="移动到..."
      :width="isMobile ? '90%' : '400px'"
    >
      <div class="move-list">
        <div
          v-for="pl in moveTargets"
          :key="pl.playlist_id"
          class="move-item"
          @click="confirmMove(pl.playlist_id)"
        >
          <el-icon :size="20"><Folder /></el-icon>
          <span class="move-name">{{ pl.name }}</span>
          <span class="move-count">{{ pl.videos.length }} 个</span>
        </div>
        <div v-if="moveTargets.length === 0" class="move-empty">
          没有其他文件夹可移动
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { AccountApi, UserPlaylist } from '../api/account';
import {
  Plus, FolderOpened, Folder, FolderAdd, VideoCamera, Edit,
  Delete, MoreFilled, Switch, Close, ArrowLeftBold, Loading, WarningFilled
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const playlists = ref<UserPlaylist[]>([]);
const loading = ref(true);
const showCreateDialog = ref(false);
const showDeleteDialog = ref(false);
const showMoveDialog = ref(false);
const newPlaylistName = ref('');
const deletingId = ref<string | null>(null);
const movingVideoId = ref<string | null>(null);
const currentFolder = ref<UserPlaylist | null>(null);
const isMobile = ref(window.innerWidth <= 480);

// 重命名
const renamingId = ref<string | null>(null);
const renamingName = ref('');
const renameInputRef = ref<HTMLInputElement | null>(null);
const createInputRef = ref<HTMLInputElement | null>(null);

const moveTargets = computed(() =>
  currentFolder.value
    ? playlists.value.filter(p => p.playlist_id !== currentFolder.value!.playlist_id)
    : []
);

const loadPlaylists = async () => {
  loading.value = true;
  try {
    playlists.value = await AccountApi.getPlaylists();
  } catch (error) {
    console.error('加载播放清单失败:', error);
  } finally {
    loading.value = false;
  }
};

const openFolder = (playlist: UserPlaylist) => {
  currentFolder.value = playlist;
};

const handleVideoClick = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleCreate = async () => {
  if (!newPlaylistName.value.trim()) return;
  try {
    const newPl = await AccountApi.createPlaylist(newPlaylistName.value.trim());
    showCreateDialog.value = false;
    newPlaylistName.value = '';
    playlists.value.push(newPl);
  } catch (error) {
    ElMessage.error('创建文件夹失败');
  }
};

const startRename = (playlist: UserPlaylist) => {
  renamingId.value = playlist.playlist_id;
  renamingName.value = playlist.name;
  nextTick(() => {
    if (renameInputRef.value) {
      const el = renameInputRef.value as unknown as HTMLElement;
      const input = el.querySelector('input');
      if (input) { input.focus(); input.select(); }
    }
  });
};

const confirmRename = async () => {
  if (!renamingId.value || !renamingName.value.trim()) {
    renamingId.value = null;
    return;
  }
  try {
    await AccountApi.updatePlaylistName(renamingId.value, renamingName.value.trim());
    const pl = playlists.value.find(p => p.playlist_id === renamingId.value);
    if (pl) pl.name = renamingName.value.trim();
    if (currentFolder.value && currentFolder.value.playlist_id === renamingId.value) {
      currentFolder.value.name = renamingName.value.trim();
    }
    renamingId.value = null;
  } catch (error) {
    ElMessage.error('重命名失败');
    renamingId.value = null;
  }
};

const handleDelete = (playlistId: string) => {
  deletingId.value = playlistId;
  showDeleteDialog.value = true;
};

const confirmDelete = async () => {
  showDeleteDialog.value = false;
  if (!deletingId.value) return;
  try {
    await AccountApi.deletePlaylist(deletingId.value);
    playlists.value = playlists.value.filter(p => p.playlist_id !== deletingId.value);
    if (currentFolder.value && currentFolder.value.playlist_id === deletingId.value) {
      currentFolder.value = null;
    }
    deletingId.value = null;
    ElMessage.success('已删除文件夹');
  } catch (error) {
    ElMessage.error('删除失败');
    deletingId.value = null;
  }
};

const handleRemoveVideo = async (videoId: string) => {
  if (!currentFolder.value) return;
  try {
    await AccountApi.removeVideoFromPlaylist(currentFolder.value.playlist_id, videoId);
    currentFolder.value.videos = currentFolder.value.videos.filter(v => v.video_id !== videoId);
    const pl = playlists.value.find(p => p.playlist_id === currentFolder.value!.playlist_id);
    if (pl) pl.videos = currentFolder.value.videos;
  } catch (error) {
    ElMessage.error('移除失败');
  }
};

const startMoveVideo = (videoId: string) => {
  if (moveTargets.value.length === 0) {
    ElMessage.info('没有其他文件夹可移动');
    return;
  }
  movingVideoId.value = videoId;
  showMoveDialog.value = true;
};

const confirmMove = async (toPlaylistId: string) => {
  if (!currentFolder.value || !movingVideoId.value) return;
  showMoveDialog.value = false;
  try {
    await AccountApi.moveVideoToPlaylist(currentFolder.value.playlist_id, toPlaylistId, movingVideoId.value);
    // 从当前视图移除
    currentFolder.value.videos = currentFolder.value.videos.filter(v => v.video_id !== movingVideoId.value);
    const pl = playlists.value.find(p => p.playlist_id === currentFolder.value!.playlist_id);
    if (pl) pl.videos = currentFolder.value.videos;
    // 添加到目标清单缓存
    const target = playlists.value.find(p => p.playlist_id === toPlaylistId);
    if (target) {
      const video = currentFolder.value.videos.find(v => v.video_id === movingVideoId.value) ||
        playlists.value.flatMap(p => p.videos).find(v => v.video_id === movingVideoId.value);
    }
    movingVideoId.value = null;
    // 重新加载以确保数据一致
    await loadPlaylists();
    // 恢复当前文件夹引用
    if (currentFolder.value) {
      const updated = playlists.value.find(p => p.playlist_id === currentFolder.value!.playlist_id);
      if (updated) currentFolder.value = updated;
    }
  } catch (error) {
    ElMessage.error('移动失败');
    movingVideoId.value = null;
  }
};

const formatTime = (timeStr: string): string => {
  try {
    const date = new Date(timeStr);
    const now = new Date();
    if (date.toDateString() === now.toDateString()) return '今天';
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) return '昨天';
    return `${date.getMonth() + 1}月${date.getDate()}日`;
  } catch {
    return timeStr;
  }
};

onMounted(() => {
  loadPlaylists();
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth <= 480;
  });
});
</script>

<style scoped>
.playlists-page {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}

/* ========== 页头 ========== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--text-color);
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-accent {
  display: inline-block;
  width: 4px;
  height: 20px;
  border-radius: 2px;
  background: linear-gradient(180deg, #409EFF, #a855f7);
}

.folder-count {
  font-size: 13px;
  color: var(--text-secondary-color);
  opacity: 0.7;
}

.create-btn {
  border-radius: 10px;
}

/* ========== 加载/空状态 ========== */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-secondary-color);
  gap: 12px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  gap: 8px;
}

.empty-icon-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--hover-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.empty-icon {
  color: var(--text-secondary-color);
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary-color);
  margin: 0 0 12px;
}

/* ========== 文件夹网格 ========== */
.folders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.folder-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
  background: var(--card-bg, rgba(255,255,255,0.03));
}

.folder-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

:global(.light) .folder-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

/* 文件夹封面 */
.folder-cover {
  position: relative;
  width: 100%;
  padding-top: 75%;
  overflow: hidden;
  background: var(--bg-secondary-color);
}

.cover-thumbs {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 2px;
}

.cover-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-thumb-placeholder {
  background: var(--border-color);
}

.cover-empty {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary-color);
  opacity: 0.3;
}

.folder-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(0deg, rgba(0,0,0,0.4) 0%, transparent 50%);
  pointer-events: none;
}

/* 文件夹信息 */
.folder-info {
  padding: 12px 14px;
}

.folder-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.folder-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.menu-trigger {
  border: none !important;
  background: transparent !important;
  color: var(--text-secondary-color) !important;
  padding: 2px 4px !important;
  min-height: auto !important;
}

.menu-trigger:hover {
  color: var(--text-color) !important;
}

.folder-meta {
  font-size: 12px;
  color: var(--text-secondary-color);
  margin: 6px 0 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-sep {
  opacity: 0.4;
}

/* ========== 文件夹内部视图 ========== */
.folder-detail-view {
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px; height: 36px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: transparent;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.back-btn:hover {
  background: var(--hover-bg-color);
  border-color: var(--primary-color);
}

.detail-title-area {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.detail-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-color);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-name-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary-color);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.edit-name-btn:hover {
  background: var(--hover-bg-color);
  color: var(--primary-color);
}

.rename-input {
  max-width: 300px;
}

.delete-folder-btn {
  flex-shrink: 0;
}

/* 文件夹空 */
.folder-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  color: var(--text-secondary-color);
  gap: 8px;
}

.folder-empty-hint {
  font-size: 13px;
  opacity: 0.7;
}

/* ========== 影片网格 ========== */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.video-card {
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
  background: var(--bg-secondary-color);
}

.video-card:hover {
  transform: translateY(-3px);
}

.video-cover {
  position: relative;
  width: 100%;
  padding-top: 140%;
  overflow: hidden;
  background: var(--border-color);
}

.video-cover img {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
}

.video-hover-actions {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.video-card:hover .video-hover-actions {
  opacity: 1;
}

.video-title {
  font-size: 12px;
  color: var(--text-color);
  margin: 0;
  padding: 8px 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

/* ========== 弹窗 ========== */
.create-input {
  margin-bottom: 4px;
}

.delete-warn {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.6;
}

.move-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.move-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  color: var(--text-color);
}

.move-item:hover {
  background: var(--hover-bg-color);
}

.move-name {
  flex: 1;
  font-size: 14px;
}

.move-count {
  font-size: 12px;
  color: var(--text-secondary-color);
}

.move-empty {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary-color);
  font-size: 14px;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .playlists-page {
    padding: 14px 10px 40px;
  }

  .page-title {
    font-size: 20px;
  }

  .folders-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
  }

  .videos-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 8px;
  }

  .detail-title {
    font-size: 17px;
  }

  .video-hover-actions {
    opacity: 1;
  }
}

@media (max-width: 480px) {
  .playlists-page {
    padding: 10px 6px 40px;
  }

  .page-title {
    font-size: 18px;
  }

  .folders-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .folder-info {
    padding: 8px 10px;
  }

  .folder-name {
    font-size: 13px;
  }

  .videos-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }

  .detail-header {
    gap: 8px;
  }

  .detail-title {
    font-size: 16px;
  }
}
</style>
