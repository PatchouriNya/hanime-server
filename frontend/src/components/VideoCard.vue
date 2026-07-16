<template>
  <div 
    class="video-card card"
    :class="customClass"
    @click="$emit('click', video.video_id)"
  >
    <div class="video-thumbnail" :class="[thumbnailClass, { 'blur-cover': shouldBlur && blurMode === 'blur', 'hide-cover': shouldBlur && blurMode === 'hide' }]">
      <img
        :src="video.cover_url"
        :alt="video.title"
        loading="lazy"
        referrerpolicy="no-referrer"
        :class="{ 'blurred': shouldBlur && blurMode === 'blur' }"
      />
      <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
      <div v-if="shouldBlur && blurMode === 'hide'" class="hide-overlay">
        <el-icon :size="48" class="hide-icon"><Hide /></el-icon>
        <span class="hide-text">图片已隐藏</span>
      </div>
      <div v-if="isVideoPreview(video)" class="video-duration">{{ video.duration }}</div>
      <div v-if="isVideoPreview(video) && video.view_count" class="video-views-badge">
        <el-icon><View /></el-icon> {{ formatViewCount(video.view_count) }}
      </div>
      <div v-if="isVideoPreview(video) && video.like_rate" class="video-like-badge">
        <svg class="thumb-icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" width="12" height="12">
          <path d="M885.9 533.7c16.8-22.2 26.1-49.4 26.1-77.7 0-44.9-25.1-87.4-65.5-111.1a67.67 67.67 0 0 0-34.3-9.3H572.4l6-122.9c1.4-29.7-9.1-57.9-29.5-79.4-20.5-21.5-48.1-33.4-77.9-33.4-52 0-98 35-111.8 85.1l-85.9 311H144c-17.7 0-32 14.3-32 32v364c0 17.7 14.3 32 32 32h601.3c9.2 0 18.2-1.8 26.5-5.4 47.6-20.3 78.3-66.8 78.3-118.4 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7-0.2-12.6-2-25.1-5.6-37.1zM184 852V568h81v284h-81z m636.4-353l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 16.5-7.2 32.2-19.6 43l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 16.5-7.2 32.2-19.6 43l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 22.4-13.2 42.6-33.6 51.8H329V564.8l99.5-360.5c5.2-18.9 22.5-32.2 42.2-32.3 7.6 0 15.1 2.2 21.1 6.7 9.9 7.4 15.2 18.6 14.6 30.5l-9.6 198.4h314.4C829 418.5 840 436.9 840 456c0 16.5-7.2 32.1-19.6 43z" fill="currentColor"></path>
        </svg>
        <span class="like-percentage">{{ video.like_rate }}</span>
        <span v-if="video.like_count" class="like-count">({{ video.like_count }})</span>
      </div>
      <div class="play-overlay">
        <el-icon v-if="showPlayIcon && !(shouldBlur && blurMode === 'hide')" :size="48"><VideoPlay /></el-icon>
      </div>
      <div
        class="favorite-btn"
        :class="{ 'is-favorited': isFavorited }"
        @click.stop="toggleFavorite"
      >
        <el-icon :size="16">
          <StarFilled v-if="isFavorited" />
          <Star v-else />
        </el-icon>
      </div>
    </div>
    <div class="video-info">
      <div class="video-title" :class="{'single-line': singleLineTitle}">{{ video.title }}</div>
      <div v-if="isVideoPreview(video) && video.studio" class="video-studio">
        {{ video.studio.name }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType, ref, onMounted} from 'vue';
import {VideoBase, VideoPreview} from '../types/video';
import { View, VideoPlay, Hide, Star, StarFilled } from '@element-plus/icons-vue';
import { useContentSettings } from '../composables/useContentSettings';
import { AccountApi } from '../api/account';
import { ElMessage } from 'element-plus';

export default defineComponent({
  name: 'VideoCard',
  components: {
    View,
    VideoPlay,
    Hide,
    Star,
    StarFilled
  },
  props: {
    video: {
      type: Object as PropType<VideoBase | VideoPreview>,
      required: true
    },
    thumbnailClass: {
      type: String,
      default: 'landscape'
    },
    customClass: {
      type: String,
      default: ''
    },
    singleLineTitle: {
      type: Boolean,
      default: false
    },
    useSvgThumb: {
      type: Boolean,
      default: false
    },
    showPlayIcon: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  setup(props) {
    const { shouldBlur, mode } = useContentSettings();
    const isFavorited = ref(false);

    const isVideoPreview = (video: VideoBase | VideoPreview): video is VideoPreview => {
      return 'duration' in video || 'view_count' in video || 'like_rate' in video || 'studio' in video;
    };

    const formatViewCount = (count: number): string => {
      if (!count) return '0';
      if (count >= 10000) {
        return `${(count / 10000).toFixed(1)}万`;
      } else if (count >= 1000) {
        return `${(count / 1000).toFixed(1)}千`;
      }
      return count.toString();
    };

    const checkFavoriteStatus = async () => {
      try {
        isFavorited.value = await AccountApi.isFavorite(props.video.video_id);
      } catch {
        // 忽略错误，可能未登录
      }
    };

    const toggleFavorite = async () => {
      try {
        if (isFavorited.value) {
          await AccountApi.removeFavorite(props.video.video_id);
          isFavorited.value = false;
          ElMessage.success('已取消收藏');
        } else {
          await AccountApi.addFavorite(
            props.video.video_id,
            props.video.title,
            props.video.cover_url || ''
          );
          isFavorited.value = true;
          ElMessage.success('已添加收藏');
        }
      } catch {
        ElMessage.error('操作失败');
      }
    };

    onMounted(checkFavoriteStatus);

    return {
      isVideoPreview,
      formatViewCount,
      shouldBlur,
      blurMode: mode,
      isFavorited,
      toggleFavorite
    };
  }
});
</script>

<style scoped>
.video-card {
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background-color: var(--bg-secondary-color);
  border-radius: 12px;
  overflow: hidden;
  animation: cardFadeInUp 0.5s ease-out forwards;
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

@keyframes cardFadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.video-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
  border-color: rgba(236, 72, 153, 0.15);
}

.video-thumbnail.landscape {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 宽高比 */
  overflow: hidden;
}

.video-thumbnail.portrait {
  position: relative;
  width: 100%;
  padding-top: 142.85%; /* 高宽比约为 7:5 */
  overflow: hidden;
}

.video-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.video-card:hover .video-thumbnail img {
  transform: scale(1.08);
}

.video-thumbnail img.blurred {
  filter: blur(20px) brightness(0.8);
  transform: scale(1.1);
}

.blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
}

.hide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary-color) 0%, var(--bg-color) 100%);
  z-index: 3;
  animation: fadeIn 0.3s ease-out;
}

.hide-icon {
  color: var(--text-secondary-color);
  margin-bottom: 8px;
}

.hide-text {
  color: var(--text-secondary-color);
  font-size: 12px;
  font-weight: 500;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(0, 0, 0, 0.5) 100%);
  opacity: 0;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-overlay .el-icon {
  color: white;
  opacity: 0;
  transform: scale(0.6);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.5));
}

.video-card:hover .play-overlay {
  opacity: 1;
}

.video-card:hover .play-overlay .el-icon {
  opacity: 1;
  transform: scale(1);
}

/* 收藏按钮 */
.favorite-btn {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 4;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.25s ease;
  color: rgba(255, 255, 255, 0.8);
}

.video-card:hover .favorite-btn {
  opacity: 1;
  transform: scale(1);
}

.favorite-btn:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.15) !important;
}

.favorite-btn.is-favorited {
  opacity: 1;
  transform: scale(1);
  background: rgba(255, 71, 87, 0.85);
  color: #fff;
}

.favorite-btn.is-favorited:hover {
  background: rgba(255, 71, 87, 1);
  transform: scale(1.15) !important;
}

/* 时长、点赞率和播放次数徽章 */
.video-duration,
.video-views-badge,
.video-like-badge {
  position: absolute;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  z-index: 2;
  display: flex;
  align-items: center;
}

.video-duration {
  bottom: 8px;
  right: 8px;
}

.video-views-badge {
  top: 8px;
  right: 8px;
}

.video-views-badge .el-icon {
  margin-right: 3px;
}

.video-like-badge {
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
}

.video-like-badge .el-icon,
.video-like-badge .thumb-icon {
  margin-right: 3px;
  vertical-align: middle;
}

.like-percentage {
  margin-right: 2px;
  vertical-align: middle;
}

.like-count {
  font-size: 8px;
  opacity: 0.8;
  vertical-align: middle;
}

.video-info {
  padding: 10px 10px 12px;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.video-title.single-line {
  -webkit-line-clamp: 1;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.video-studio {
  font-size: 12px;
  color: var(--text-secondary-color);
}

/* 当前播放中的视频卡片样式 */
.current-video {
  border: 2px solid var(--primary-color);
  position: relative;
}

.current-video::after {
  content: '当前播放';
  position: absolute;
  top: 0;
  left: 0;
  background: var(--primary-color);
  color: white;
  font-size: 10px;
  padding: 2px 5px;
  border-bottom-right-radius: 8px;
  z-index: 3;
}

/* PC端大气布局 */
@media (min-width: 769px) {
  .video-info {
    padding: 12px 12px 14px;
  }

  .video-title {
    font-size: 15px;
  }

  .video-studio {
    font-size: 13px;
  }

  .video-duration,
  .video-views-badge,
  .video-like-badge {
    padding: 3px 8px;
    font-size: 11px;
  }

  .favorite-btn {
    width: 32px;
    height: 32px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-card { border-radius: 10px; }
  .video-title { font-size: 13px; }
  .video-studio { font-size: 11px; }
}

@media (max-width: 480px) {
  .video-card { border-radius: 8px; }
  .video-title { font-size: 12px; }
  .video-studio { font-size: 10px; }
  .video-info { padding: 8px 8px 10px; }
  .video-duration,
  .video-like-badge,
  .video-views-badge {
    padding: 2px 4px;
    font-size: 9px;
  }
}
</style> 