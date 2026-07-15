<template>
  <div class="watch-later-page">
    <div class="page-header">
      <h1 class="page-title">稍后观看</h1>
      <div class="header-actions">
        <el-button v-if="watchLater.length > 0" @click="showConfirmDialog = true" type="danger" plain>
          <el-icon><Delete /></el-icon> 清空列表
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="watchLater.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <Clock />
      </el-icon>
      <p class="empty-text">暂无稍后观看的影片</p>
      <p class="empty-hint">去浏览影片，添加到稍后观看列表</p>
    </div>

    <div v-else class="video-grid">
      <video-card
        v-for="video in watchLater"
        :key="video.video_id"
        :video="video"
        thumbnail-class="portrait"
        show-play-icon
        @click="handleVideoClick"
      >
        <template #actions>
          <el-button
            size="small"
            @click.stop="handleStartWatching(video.video_id)"
            type="primary"
          >
            开始观看
          </el-button>
          <el-button
            icon="Delete"
            size="small"
            @click.stop="handleRemove(video.video_id)"
            type="danger"
            plain
          >
            移除
          </el-button>
        </template>
      </video-card>
    </div>

    <el-dialog
      v-model="showConfirmDialog"
      title="清空稍后观看"
      width="30%"
    >
      <span>确定要清空所有稍后观看的影片吗？此操作不可撤销。</span>
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
import { AccountApi, UserVideoItem } from '../api/account';
import VideoCard from '../components/VideoCard.vue';
import { Clock, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const watchLater = ref<UserVideoItem[]>([]);
const loading = ref(true);
const showConfirmDialog = ref(false);

const loadWatchLater = async () => {
  loading.value = true;
  try {
    watchLater.value = await AccountApi.getWatchLater();
  } catch (error) {
    console.error('加载稍后观看失败:', error);
    ElMessage.error('加载稍后观看失败');
  } finally {
    loading.value = false;
  }
};

const handleVideoClick = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleStartWatching = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleRemove = async (videoId: string) => {
  try {
    await AccountApi.removeWatchLater(videoId);
    watchLater.value = watchLater.value.filter(v => v.video_id !== videoId);
    ElMessage.success('已移除此影片');
  } catch (error) {
    console.error('移除失败:', error);
    ElMessage.error('移除失败');
  }
};

const handleClearAll = async () => {
  showConfirmDialog.value = false;
  try {
    for (const video of watchLater.value) {
      await AccountApi.removeWatchLater(video.video_id);
    }
    watchLater.value = [];
    ElMessage.success('已清空稍后观看列表');
  } catch (error) {
    console.error('清空列表失败:', error);
    ElMessage.error('清空列表失败');
  }
};

onMounted(loadWatchLater);
</script>

<style scoped>
.watch-later-page {
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

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
}

@media (max-width: 768px) {
  .watch-later-page {
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
  .watch-later-page {
    padding: 5px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
}
</style>
