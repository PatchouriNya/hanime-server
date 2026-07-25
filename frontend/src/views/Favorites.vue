<template>
  <div class="favorites-page">
    <div class="page-header">
      <h1 class="page-title">收藏的番剧</h1>
      <div class="header-actions">
        <el-button v-if="favorites.length > 0" @click="showConfirmDialog = true" type="danger" plain>
          <el-icon><Delete /></el-icon> 清空收藏
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else-if="favorites.length === 0" class="empty-container">
      <el-icon :size="120" class="empty-icon">
        <Star />
      </el-icon>
      <p class="empty-text">暂无收藏的影片</p>
      <p class="empty-hint">去浏览影片，点击爱心图标添加收藏</p>
    </div>

    <div v-else class="video-grid">
      <video-card
        v-for="video in favorites"
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
      title="清空收藏"
      width="30%"
    >
      <span>确定要清空所有收藏的影片吗？此操作不可撤销。</span>
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
import { Star, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const favorites = ref<UserVideoItem[]>([]);
const loading = ref(true);
const showConfirmDialog = ref(false);

const loadFavorites = async () => {
  loading.value = true;
  try {
    favorites.value = await AccountApi.getFavorites();
  } catch (error) {
    console.error('加载收藏失败:', error);
    ElMessage.error('加载收藏失败');
  } finally {
    loading.value = false;
  }
};

const handleVideoClick = (videoId: string) => {
  router.push(`/video/${videoId}`);
};

const handleRemove = async (videoId: string) => {
  try {
    await AccountApi.removeFavorite(videoId);
    favorites.value = favorites.value.filter(v => v.video_id !== videoId);
    ElMessage.success('已移除收藏');
  } catch (error) {
    console.error('移除收藏失败:', error);
    ElMessage.error('移除收藏失败');
  }
};

const handleClearAll = async () => {
  showConfirmDialog.value = false;
  try {
    for (const video of favorites.value) {
      await AccountApi.removeFavorite(video.video_id);
    }
    favorites.value = [];
    ElMessage.success('已清空所有收藏');
  } catch (error) {
    console.error('清空收藏失败:', error);
    ElMessage.error('清空收藏失败');
  }
};

onMounted(loadFavorites);
</script>

<style scoped>
.favorites-page {
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
  .favorites-page {
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
}

@media (max-width: 768px) {
  .favorites-page {
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
  .favorites-page {
    padding: 5px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
}
</style>
