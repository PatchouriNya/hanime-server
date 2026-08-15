<template>
  <div class="subscriptions-page">
    <div class="page-header">
      <h1 class="page-title">追更订阅</h1>
      <p class="page-subtitle">订阅番剧系列，有新集时提醒</p>
      <div class="header-actions">
        <el-button @click="loadAll" :loading="loading">
          <el-icon><Refresh /></el-icon> 检查更新
        </el-button>
      </div>
    </div>

    <div v-if="loading && items.length === 0" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="items.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <Bell />
      </el-icon>
      <p class="empty-text">暂无订阅</p>
      <p class="empty-hint">在下载中心的番剧卡片上点击"订阅"，有新集时这里会提醒</p>
    </div>

    <div v-else class="subscription-grid">
      <div
        v-for="item in items"
        :key="item.series_name"
        class="subscription-card"
        :class="{ 'has-new': item.has_new }"
      >
        <div class="card-top">
          <div class="series-cover" v-if="item.latest_episode?.cover_url">
            <img
              :src="getCoverUrl(item.latest_episode.video_id)"
              :alt="item.series_name"
              loading="lazy"
              referrerpolicy="no-referrer"
              @error="handleCoverError"
            />
            <div v-if="item.has_new" class="new-badge">有新集</div>
          </div>
          <div class="series-cover placeholder" v-else>
            <el-icon :size="40"><Film /></el-icon>
            <div v-if="item.has_new" class="new-badge">有新集</div>
          </div>
          <div class="series-info">
            <div class="series-name" :title="item.series_name">{{ item.series_name }}</div>
            <div class="series-meta">
              <span class="meta-item">已下载 {{ item.downloaded_count || 0 }} 集</span>
              <span v-if="item.source_episode" class="meta-item">最新至第 {{ item.source_episode }} 集</span>
            </div>
            <div v-if="item.has_new && item.latest_episode" class="new-episode-title">
              最新：{{ item.latest_episode.title }}
            </div>
            <div v-if="item.error" class="check-error">检查失败，请稍后重试</div>
          </div>
        </div>
        <div class="card-actions">
          <el-button
            v-if="item.has_new && item.latest_episode"
            type="primary"
            size="small"
            :loading="downloadingIds.includes(item.latest_episode.video_id)"
            @click="handleDownloadLatest(item)"
          >
            <el-icon><Download /></el-icon> 下载最新集
          </el-button>
          <el-button
            v-if="item.latest_episode"
            size="small"
            @click="goToVideo(item.latest_episode.video_id)"
          >
            查看详情
          </el-button>
          <el-button size="small" type="danger" plain @click="handleUnsubscribe(item.series_name)">
            取消订阅
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { AccountApi } from '../api/account';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Bell, Refresh, Film, Download } from '@element-plus/icons-vue';
import { useDownloadStore } from '../stores/download';

const router = useRouter();
const downloadStore = useDownloadStore();
const loading = ref(false);
const items = ref<any[]>([]);
const downloadingIds = ref<string[]>([]);

const defaultCover = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MCIgaGVpZ2h0PSIxMTQiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMyNzI3MmEiLz48L3N2Zz4=';

// 封面走本地封面接口（无封面时用默认图）
const getCoverUrl = (videoId: string) => {
  const token = localStorage.getItem('token');
  return `/api/downloads/cover/${videoId}${token ? `?token=${token}` : ''}`;
};

const handleCoverError = (event: Event) => {
  (event.target as HTMLImageElement).src = defaultCover;
};

const loadAll = async () => {
  loading.value = true;
  try {
    const subscriptions = await AccountApi.getSubscriptions();
    if (subscriptions.length === 0) {
      items.value = [];
      return;
    }
    const results = await AccountApi.checkSubscriptions();
    items.value = results;
  } catch (error) {
    console.error('加载追更列表失败:', error);
    ElMessage.error('加载追更列表失败');
  } finally {
    loading.value = false;
  }
};

const handleDownloadLatest = async (item: any) => {
  const videoId = item.latest_episode.video_id;
  if (!videoId) return;
  downloadingIds.value.push(videoId);
  try {
    const ok = await downloadStore.startDownload(videoId);
    if (ok) {
      ElMessage.success('已开始下载最新集');
      item.has_new = false;
    }
  } finally {
    downloadingIds.value = downloadingIds.value.filter(id => id !== videoId);
  }
};

const handleUnsubscribe = async (seriesName: string) => {
  try {
    await ElMessageBox.confirm(`确定取消订阅「${seriesName}」吗？`, '取消订阅', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
  } catch {
    return;
  }
  try {
    await AccountApi.removeSubscription(seriesName);
    items.value = items.value.filter(i => i.series_name !== seriesName);
    ElMessage.success('已取消订阅');
  } catch (error) {
    console.error('取消订阅失败:', error);
    ElMessage.error('取消订阅失败');
  }
};

const goToVideo = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

onMounted(loadAll);
</script>

<style scoped>
.subscriptions-page {
  width: 100%;
  max-width: 1200px;
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

.subscription-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.subscription-card {
  background-color: var(--bg-secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  transition: box-shadow 0.3s, border-color 0.3s;
}

.subscription-card.has-new {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.card-top {
  display: flex;
  gap: 14px;
}

.series-cover {
  position: relative;
  flex: 0 0 80px;
  width: 80px;
  height: 114px;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.06);
}

.series-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.series-cover.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary-color);
}

.new-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background-color: var(--color-primary);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.series-info {
  flex: 1;
  min-width: 0;
}

.series-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.series-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item {
  font-size: 12px;
  color: var(--text-secondary-color);
}

.new-episode-title {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.check-error {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-error);
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
}

@media (min-width: 769px) {
  .subscriptions-page {
    padding: 32px 28px;
  }

  .page-title {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .subscriptions-page {
    padding: 10px;
  }

  .subscription-grid {
    grid-template-columns: 1fr;
  }
}
</style>
