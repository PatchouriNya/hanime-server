<template>
  <div class="library-page">
    <div class="page-header">
      <h1 class="page-title">媒体库</h1>
      <p class="page-subtitle">已下载番剧的海报墙，可本地评分与备注</p>
      <div class="header-actions">
        <el-button @click="loadLibrary" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div v-if="loading && groups.length === 0" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="groups.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <Film />
      </el-icon>
      <p class="empty-text">媒体库为空</p>
      <p class="empty-hint">下载番剧后，它们会以海报墙的形式展示在这里</p>
    </div>

    <div v-else class="library-grid">
      <div
        v-for="group in groups"
        :key="group.series_name"
        class="library-card"
        @click="openDetail(group)"
      >
        <div class="poster-wrap">
          <img
            v-if="group.cover_url"
            :src="getCoverUrl(group.cover_url)"
            :alt="group.series_name"
            loading="lazy"
            referrerpolicy="no-referrer"
            @error="handleCoverError"
          />
          <div v-else class="poster-placeholder">
            <el-icon :size="40"><Film /></el-icon>
          </div>
          <div class="episode-badge">{{ group.downloads.length }} 集</div>
          <div v-if="getRating(group.series_name) > 0" class="rating-badge">
            <el-icon><StarFilled /></el-icon> {{ getRating(group.series_name) }}
          </div>
        </div>
        <div class="card-info">
          <div class="series-title" :title="group.series_name">{{ group.series_name }}</div>
          <div v-if="getNote(group.series_name)" class="series-note" :title="getNote(group.series_name)">
            {{ getNote(group.series_name) }}
          </div>
          <div class="series-size">{{ formatFileSize(group.total_size) }}</div>
        </div>
      </div>
    </div>

    <!-- 系列详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="currentGroup?.series_name || '系列详情'"
      :width="isMobile ? '95%' : '620px'"
      destroy-on-close
    >
      <div v-if="currentGroup" class="detail-content">
        <div class="detail-top">
          <div class="detail-cover">
            <img
              v-if="currentGroup.cover_url"
              :src="getCoverUrl(currentGroup.cover_url)"
              alt=""
              referrerpolicy="no-referrer"
              @error="handleCoverError"
            />
          </div>
          <div class="detail-meta">
            <p class="meta-line">共 {{ currentGroup.downloads.length }} 集</p>
            <p class="meta-line">大小 {{ formatFileSize(currentGroup.total_size) }}</p>
            <div class="rating-row">
              <span class="rating-label">我的评分</span>
              <el-rate v-model="localRating" :max="10" show-score allow-half @change="saveDetail" />
            </div>
            <div class="note-row">
              <el-input
                v-model="localNote"
                type="textarea"
                :rows="2"
                placeholder="添加备注…"
                @blur="saveDetail"
              />
            </div>
          </div>
        </div>
        <el-divider />
        <div class="episode-list">
          <div
            v-for="dl in currentGroup.downloads"
            :key="dl.video_id"
            class="episode-row"
            @click="playEpisode(dl)"
          >
            <div class="episode-name">
              <el-icon v-if="dl.status === 'completed'" style="color: var(--color-success);"><VideoPlay /></el-icon>
              <el-icon v-else style="color: var(--color-warning);"><Loading /></el-icon>
              <span>{{ dl.title || extractFilename(dl.filename) }}</span>
            </div>
            <el-tag size="small" :type="getStatusType(dl.status)">{{ getStatusText(dl.status) }}</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import request from '../utils/request';
import { DownloadApi } from '../api/download';
import { ElMessage } from 'element-plus';
import { Refresh, Film, StarFilled, VideoPlay, Loading } from '@element-plus/icons-vue';

const router = useRouter();
const loading = ref(false);
const groups = ref<any[]>([]);
const detailVisible = ref(false);
const currentGroup = ref<any>(null);
const isMobile = ref(window.innerWidth <= 768);

// 本地评分/备注（存用户设置 mediaLibrary 字段）
const mediaLibrary = ref<Record<string, { rating: number; note: string }>>({});
const localRating = ref(0);
const localNote = ref('');

const defaultCover = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MCIgaGVpZ2h0PSIxMTQiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMyNzI3MmEiLz48L3N2Zz4=';

const getCoverUrl = (coverUrl: string) => {
  // groups 接口返回的 cover_url 可能是完整 URL 或 video_id，统一走本地封面接口
  const token = localStorage.getItem('token');
  return `/api/downloads/cover/${coverUrl}${token ? `?token=${token}` : ''}`;
};

const handleCoverError = (event: Event) => {
  (event.target as HTMLImageElement).src = defaultCover;
};

const formatFileSize = (bytes: number): string => {
  return DownloadApi.formatFileSize(bytes || 0);
};

const getRating = (seriesName: string): number => {
  return mediaLibrary.value[seriesName]?.rating || 0;
};

const getNote = (seriesName: string): string => {
  return mediaLibrary.value[seriesName]?.note || '';
};

const extractFilename = (filename: string): string => {
  if (!filename) return '';
  const parts = filename.split('/');
  return parts[parts.length - 1];
};

const getStatusType = (status: string): 'success' | 'primary' | 'danger' | 'info' | 'warning' => {
  switch (status) {
    case 'completed': return 'success';
    case 'downloading': return 'primary';
    case 'error': return 'danger';
    case 'paused': return 'warning';
    default: return 'info';
  }
};

const getStatusText = (status: string): string => {
  const map: Record<string, string> = {
    pending: '等待中', downloading: '下载中', paused: '已暂停',
    completed: '已完成', cancelled: '已取消', error: '失败'
  };
  return map[status] || status;
};

const loadMediaLibrary = async () => {
  try {
    const response = await request.get('/accounts/me/settings');
    if (response.data?.success && response.data.settings?.mediaLibrary) {
      mediaLibrary.value = response.data.settings.mediaLibrary;
    }
  } catch (e) {
    console.error('加载媒体库备注失败:', e);
  }
};

const saveMediaLibrary = async () => {
  try {
    await request.post('/accounts/me/settings', { mediaLibrary: mediaLibrary.value });
  } catch (e) {
    console.error('保存媒体库备注失败:', e);
  }
};

const loadLibrary = async () => {
  loading.value = true;
  try {
    const data = await DownloadApi.getDownloadGroups();
    groups.value = (data || []).filter((g: any) => (g.downloads?.length || 0) > 0);
  } catch (error) {
    console.error('加载媒体库失败:', error);
    ElMessage.error('加载媒体库失败');
  } finally {
    loading.value = false;
  }
};

const openDetail = (group: any) => {
  currentGroup.value = group;
  localRating.value = getRating(group.series_name);
  localNote.value = getNote(group.series_name);
  detailVisible.value = true;
};

const saveDetail = () => {
  if (!currentGroup.value) return;
  const seriesName = currentGroup.value.series_name;
  if (localRating.value > 0 || localNote.value.trim()) {
    mediaLibrary.value = {
      ...mediaLibrary.value,
      [seriesName]: { rating: localRating.value, note: localNote.value.trim() }
    };
  } else {
    const next = { ...mediaLibrary.value };
    delete next[seriesName];
    mediaLibrary.value = next;
  }
  saveMediaLibrary();
};

const playEpisode = (dl: any) => {
  if (dl.status === 'completed') {
    router.push(`/video/${dl.video_id}`);
  }
};

onMounted(async () => {
  await Promise.all([loadLibrary(), loadMediaLibrary()]);
});
</script>

<style scoped>
.library-page {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary-color);
  margin: 4px 0 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container,
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

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.library-card {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  background-color: var(--bg-secondary-color);
  border: 1px solid var(--border-color);
  transition: transform 0.3s, box-shadow 0.3s;
}

.library-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.poster-wrap {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.06);
}

.poster-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.poster-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary-color);
}

.episode-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background-color: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
}

.rating-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: rgba(236, 72, 153, 0.9);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 3px;
}

.card-info {
  padding: 10px 12px 12px;
}

.series-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.series-note {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.series-size {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color);
}

.detail-content {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-top {
  display: flex;
  gap: 16px;
}

.detail-cover {
  flex: 0 0 120px;
  width: 120px;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.06);
}

.detail-cover img {
  width: 100%;
  display: block;
  aspect-ratio: 2 / 3;
  object-fit: cover;
}

.detail-meta {
  flex: 1;
  min-width: 0;
}

.meta-line {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--text-secondary-color);
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0;
}

.rating-label {
  font-size: 13px;
  color: var(--text-color);
  white-space: nowrap;
}

.note-row {
  margin-top: 8px;
}

.episode-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background-color 0.2s;
}

.episode-row:hover {
  background-color: rgba(255, 255, 255, 0.08);
}

.episode-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-color);
  min-width: 0;
}

.episode-name span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (min-width: 769px) {
  .library-page {
    padding: 32px 28px;
  }

  .page-title {
    font-size: 28px;
  }

  .library-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .library-page {
    padding: 10px;
  }

  .library-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
  }
}
</style>
