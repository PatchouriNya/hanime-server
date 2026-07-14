<template>
  <div class="playlists-page">
    <div class="page-header">
      <h1 class="page-title">播放清单</h1>
      <div class="header-actions">
        <el-button @click="showCreateDialog = true" type="primary">
          <el-icon><Plus /></el-icon> 创建清单
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="playlists.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <FolderOpened />
      </el-icon>
      <p class="empty-text">暂无播放清单</p>
      <p class="empty-hint">点击上方按钮创建新的播放清单</p>
    </div>

    <div v-else class="playlists-container">
      <div
        v-for="playlist in playlists"
        :key="playlist.playlist_id"
        class="playlist-card"
      >
        <div class="playlist-header">
          <h3 class="playlist-name" :class="{ editing: editingId === playlist.playlist_id }">
            <span v-if="editingId !== playlist.playlist_id">{{ playlist.name }}</span>
            <el-input
              v-else
              v-model="editingName"
              class="edit-input"
              @blur="saveEdit(playlist.playlist_id)"
              @keyup.enter="saveEdit(playlist.playlist_id)"
              ref="editInputRef"
            />
          </h3>
          <div class="playlist-actions">
            <el-button
              icon="Edit"
              size="small"
              @click="startEdit(playlist)"
              v-if="editingId !== playlist.playlist_id"
            >
              重命名
            </el-button>
            <el-button
              icon="Delete"
              size="small"
              type="danger"
              @click="handleDelete(playlist.playlist_id)"
            >
              删除
            </el-button>
          </div>
        </div>

        <div class="playlist-info">
          <span class="video-count">{{ playlist.videos.length }} 个影片</span>
          <span class="updated-time">更新于 {{ formatTime(playlist.updated_at) }}</span>
        </div>

        <div v-if="playlist.videos.length > 0" class="playlist-videos">
          <video-card
            v-for="video in playlist.videos"
            :key="video.video_id"
            :video="video"
            thumbnail-class="portrait"
            show-play-icon
            @click="handleVideoClick"
          >
            <template #actions>
              <el-button
                icon="Delete"
                size="small"
                @click.stop="handleRemoveVideo(playlist.playlist_id, video.video_id)"
                type="danger"
                plain
              >
                移除
              </el-button>
            </template>
          </video-card>
        </div>

        <div v-else class="playlist-empty">
          <p>此清单暂无影片</p>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showCreateDialog"
      title="创建播放清单"
      width="30%"
    >
      <el-input
        v-model="newPlaylistName"
        placeholder="请输入清单名称"
        class="name-input"
        @keyup.enter="handleCreate"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreate">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showDeleteDialog"
      title="删除播放清单"
      width="30%"
    >
      <span>确定要删除此播放清单吗？此操作不可撤销。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDeleteDialog = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { AccountApi, UserPlaylist } from '../api/account';
import VideoCard from '../components/VideoCard.vue';
import { Plus, FolderOpened } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const playlists = ref<UserPlaylist[]>([]);
const loading = ref(true);
const showCreateDialog = ref(false);
const showDeleteDialog = ref(false);
const newPlaylistName = ref('');
const editingId = ref<string | null>(null);
const editingName = ref('');
const deletingId = ref<string | null>(null);
const editInputRef = ref<HTMLElement | null>(null);

const loadPlaylists = async () => {
  loading.value = true;
  try {
    playlists.value = await AccountApi.getPlaylists();
  } catch (error) {
    console.error('加载播放清单失败:', error);
    ElMessage.error('加载播放清单失败');
  } finally {
    loading.value = false;
  }
};

const handleVideoClick = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleCreate = async () => {
  if (!newPlaylistName.value.trim()) {
    ElMessage.warning('请输入清单名称');
    return;
  }

  try {
    await AccountApi.createPlaylist(newPlaylistName.value.trim());
    showCreateDialog.value = false;
    newPlaylistName.value = '';
    await loadPlaylists();
    ElMessage.success('创建播放清单成功');
  } catch (error) {
    console.error('创建播放清单失败:', error);
    ElMessage.error('创建播放清单失败');
  }
};

const startEdit = (playlist: UserPlaylist) => {
  editingId.value = playlist.playlist_id;
  editingName.value = playlist.name;
  nextTick(() => {
    if (editInputRef.value) {
      (editInputRef.value as HTMLInputElement).focus();
      (editInputRef.value as HTMLInputElement).select();
    }
  });
};

const saveEdit = async (playlistId: string) => {
  if (!editingName.value.trim()) {
    ElMessage.warning('名称不能为空');
    return;
  }

  try {
    await AccountApi.updatePlaylistName(playlistId, editingName.value.trim());
    editingId.value = null;
    await loadPlaylists();
    ElMessage.success('更新名称成功');
  } catch (error) {
    console.error('更新名称失败:', error);
    ElMessage.error('更新名称失败');
    editingId.value = null;
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
    deletingId.value = null;
    ElMessage.success('删除播放清单成功');
  } catch (error) {
    console.error('删除播放清单失败:', error);
    ElMessage.error('删除播放清单失败');
    deletingId.value = null;
  }
};

const handleRemoveVideo = async (playlistId: string, videoId: string) => {
  try {
    await AccountApi.removeVideoFromPlaylist(playlistId, videoId);
    const playlist = playlists.value.find(p => p.playlist_id === playlistId);
    if (playlist) {
      playlist.videos = playlist.videos.filter(v => v.video_id !== videoId);
    }
    ElMessage.success('已从清单移除影片');
  } catch (error) {
    console.error('移除影片失败:', error);
    ElMessage.error('移除影片失败');
  }
};

const formatTime = (timeStr: string): string => {
  try {
    const date = new Date(timeStr);
    return `${date.getMonth() + 1}月${date.getDate()}日`;
  } catch {
    return timeStr;
  }
};

onMounted(loadPlaylists);
</script>

<style scoped>
.playlists-page {
  width: 100%;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-icon {
  color: var(--text-secondary-color);
  margin-bottom: 20px;
}

.empty-text {
  font-size: 18px;
  color: var(--text-color);
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 14px;
  color: var(--text-secondary-color);
}

.playlists-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.playlist-card {
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  padding: 15px;
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.playlist-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.edit-input {
  width: 200px;
}

.playlist-actions {
  display: flex;
  gap: 5px;
}

.playlist-info {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  font-size: 13px;
  color: var(--text-secondary-color);
}

.playlist-videos {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.playlist-empty {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary-color);
}

.name-input {
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .playlists-page {
    padding: 10px;
  }

  .page-title {
    font-size: 20px;
  }

  .playlist-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .playlist-videos {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .playlists-page {
    padding: 5px;
  }

  .playlist-videos {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 6px;
  }
}
</style>
