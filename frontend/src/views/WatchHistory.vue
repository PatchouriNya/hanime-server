<template>
  <div class="watch-history-page">
    <div class="page-header">
      <h1 class="page-title">观看历史</h1>
      <div class="header-actions">
        <el-button v-if="history.length > 0" @click="showConfirmDialog = true" type="danger" plain>
          <el-icon><Delete /></el-icon> 清空历史
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="history.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <Clock />
      </el-icon>
      <p class="empty-text">暂无观看历史</p>
      <p class="empty-hint">去观看影片，历史记录会自动保存</p>
    </div>

    <div v-else class="video-grid">
      <div
        v-for="item in history"
        :key="item.video_id"
        class="history-item"
        @click="handleVideoClick(item.video_id)"
      >
        <video-card
          :video="item"
          thumbnail-class="portrait"
          show-play-icon
        />
        <div v-if="getProgressPercent(item) > 0" class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${getProgressPercent(item)}%` }"></div>
          </div>
          <span class="progress-text">{{ getProgressText(item) }}</span>
        </div>
        <div class="history-actions">
          <!-- v4.0.0: 续播按钮（详情页会自动从上次位置继续播放） -->
          <el-button
            v-if="getProgressPercent(item) > 0"
            size="small"
            type="primary"
            plain
            @click.stop="handleContinue(item.video_id)"
          >
            <el-icon><VideoPlay /></el-icon> 继续观看
          </el-button>
          <el-button
            icon="Delete"
            size="small"
            @click.stop="handleRemove(item.video_id)"
            type="danger"
            plain
          >
            移除
          </el-button>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showConfirmDialog"
      title="清空观看历史"
      width="30%"
    >
      <span>确定要清空所有观看历史吗？此操作不可撤销。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showConfirmDialog = false">取消</el-button>
          <el-button type="danger" @click="handleClearAll">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { AccountApi, WatchHistoryItem } from '../api/account';
import VideoCard from '../components/VideoCard.vue';
import { Clock, Delete, VideoPlay } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const history = ref<WatchHistoryItem[]>([]);
const loading = ref(true);
const showConfirmDialog = ref(false);

const loadHistory = async () => {
  loading.value = true;
  try {
    history.value = await AccountApi.getWatchHistory();
  } catch (error) {
    console.error('加载观看历史失败:', error);
    ElMessage.error('加载观看历史失败');
  } finally {
    loading.value = false;
  }
};

const handleVideoClick = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

// v4.0.0: 观看历史进度（秒）→ 百分比。duration 为总秒数字符串
const getProgressPercent = (item: WatchHistoryItem): number => {
  if (!item.progress || item.progress <= 0) return 0;
  const durationSec = parseInt(item.duration || '0', 10);
  if (durationSec > 0) {
    return Math.min(100, Math.round((item.progress / durationSec) * 100));
  }
  // 没有时长信息时粗略展示（按 30 分钟上限）
  return Math.min(100, Math.round((item.progress / 1800) * 100));
};

const getProgressText = (item: WatchHistoryItem): string => {
  if (!item.progress || item.progress <= 0) return '';
  const durationSec = parseInt(item.duration || '0', 10);
  if (durationSec > 0) {
    return `已观看 ${getProgressPercent(item)}%`;
  }
  const minutes = Math.max(1, Math.round(item.progress / 60));
  return `已观看 ${minutes} 分钟`;
};

// v4.0.0: 续播——跳转详情页，详情页会自动从上次位置继续播放
const handleContinue = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleRemove = async (videoId: string) => {
  try {
    await AccountApi.removeWatchHistory(videoId);
    history.value = history.value.filter(v => v.video_id !== videoId);
    ElMessage.success('已移除历史记录');
  } catch (error) {
    console.error('移除历史记录失败:', error);
    ElMessage.error('移除历史记录失败');
  }
};

const handleClearAll = async () => {
  showConfirmDialog.value = false;
  try {
    await AccountApi.clearWatchHistory();
    history.value = [];
    ElMessage.success('已清空观看历史');
  } catch (error) {
    console.error('清空观看历史失败:', error);
    ElMessage.error('清空观看历史失败');
  }
};

onMounted(loadHistory);
</script>

<style scoped>
.watch-history-page {
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

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 16px;
}

@media (min-width: 769px) {
  .watch-history-page {
    padding: 32px 28px;
  }

  .page-title {
    font-size: 28px;
  }

  .page-header {
    margin-bottom: 28px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
  }

  .empty-text {
    font-size: 22px;
  }

  .empty-hint {
    font-size: 16px;
  }

  .progress-text {
    font-size: 12px;
  }
}

.history-item {
  position: relative;
}

.progress-bar-container {
  padding: 0 10px;
  margin-top: -5px;
}

.progress-bar {
  height: 4px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 2px;
  transition: width 0.3s;
}

.progress-text {
  display: block;
  font-size: 11px;
  color: var(--text-secondary-color);
  margin-top: 4px;
}

.history-actions {
  padding: 5px 10px 10px;
}

@media (max-width: 768px) {
  .watch-history-page {
    padding: 10px;
  }

  .page-title {
    font-size: 20px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .watch-history-page {
    padding: 5px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
}
</style>
