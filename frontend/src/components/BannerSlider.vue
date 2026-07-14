<template>
  <div class="banner-container">
    <div v-if="banner && banner.cover_url" class="banner-content">
      <div class="banner-image-container">
        <img
          :src="banner.cover_url"
          :alt="banner.title"
          class="banner-image"
          loading="lazy"
          referrerpolicy="no-referrer"
        />
        <div class="banner-overlay"></div>
      </div>
      <div class="banner-info">
        <div class="banner-text-content">
          <h2 class="banner-title">{{ banner.title }}</h2>
          <p v-if="banner.description" class="banner-description">{{ banner.description }}</p>
        </div>
        <div class="banner-actions">
          <div class="arrow-button" @click.stop="handleBannerClick(banner.video_id)">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </div>
          <div class="refresh-button" :class="{ spinning: isRefreshing }" @click.stop="$emit('refresh')" title="刷新推荐">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </div>
        </div>
      </div>
    </div>
    <!-- 骨架屏 -->
    <div v-else class="banner-skeleton">
      <el-skeleton-item variant="image" style="width: 100%; height: 100%;" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { BannerVideo } from '../types/video';
import { useRouter } from 'vue-router';

export default defineComponent({
  name: 'BannerSlider',
  props: {
    banner: {
      type: Object as PropType<BannerVideo>,
      required: true,
    },
    isRefreshing: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['refresh'],
  setup() {
    const router = useRouter();

    const handleBannerClick = (videoId: string) => {
      router.push(`/video/${videoId}`);
    };

    return {
      handleBannerClick
    };
  },
});
</script>

<style scoped>
.banner-container {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  position: relative;
}

.banner-content {
  position: relative;
  height: 380px;
  transition: transform 0.3s;
  background-color: #27272a;
}

.banner-image-container {
  position: relative;
  width: 100%;
  height: 380px;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.9) 0%,
    rgba(0, 0, 0, 0.6) 30%,
    rgba(0, 0, 0, 0.3) 60%,
    rgba(0, 0, 0, 0.1) 100%
  );
}

.banner-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 15px;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(
    to right,
    rgba(0, 0, 0, 0.4) 0%,
    rgba(0, 0, 0, 0.3) 70%,
    rgba(236, 72, 153, 0.2) 100%
  );
  backdrop-filter: blur(1px);
}

.banner-text-content {
  flex: 1;
  margin-right: 15px;
  max-width: 75%;
}

.banner-title {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #fff;
  font-weight: 700;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.banner-description {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.banner-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.arrow-button {
  width: 50px;
  height: 50px;
  background: transparent;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 15;
  transition: all 0.3s;
  flex-shrink: 0;
}

.arrow-button svg {
  color: rgba(236, 72, 153, 1.0);
  filter: drop-shadow(0 0 8px rgba(0, 0, 0, 0.5));
}

.arrow-button:hover {
  transform: translateX(5px);
}

.refresh-button {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s;
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
}

.refresh-button:hover {
  background: rgba(236, 72, 153, 0.3);
  border-color: #ec4899;
  color: #ec4899;
  transform: scale(1.08);
}

.refresh-button:active {
  transform: scale(0.95);
}

.refresh-button.spinning {
  pointer-events: none;
  opacity: 0.5;
}

.refresh-button.spinning svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.banner-skeleton {
  width: 100%;
  height: 380px;
  border-radius: 8px;
  overflow: hidden;
  background-color: #27272a;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .banner-content,
  .banner-image-container {
    height: 280px;
  }

  .banner-info {
    padding: 15px;
  }

  .banner-text-content {
    max-width: 75%;
  }

  .banner-title {
    font-size: 20px;
    margin-bottom: 8px;
  }

  .banner-description {
    font-size: 14px;
    -webkit-line-clamp: 2;
  }

  .arrow-button {
    width: 40px;
    height: 40px;
  }

  .arrow-button svg {
    width: 28px;
    height: 28px;
  }

  .refresh-button {
    width: 36px;
    height: 36px;
  }

  .refresh-button svg {
    width: 20px;
    height: 20px;
  }

  .banner-skeleton {
    height: 280px;
  }
}

@media (max-width: 480px) {
  .banner-content,
  .banner-image-container {
    height: 200px;
  }

  .banner-info {
    padding: 10px;
  }

  .banner-text-content {
    max-width: 80%;
  }

  .banner-title {
    font-size: 16px;
    margin-bottom: 4px;
  }

  .banner-description {
    font-size: 12px;
    -webkit-line-clamp: 2;
  }

  .arrow-button {
    width: 36px;
    height: 36px;
  }

  .arrow-button svg {
    width: 24px;
    height: 24px;
  }

  .refresh-button {
    width: 32px;
    height: 32px;
  }

  .refresh-button svg {
    width: 18px;
    height: 18px;
  }

  .banner-skeleton {
    height: 200px;
  }
}
</style> 