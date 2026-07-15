<template>
  <div
    class="banner-container"
    @mouseenter="pauseAutoPlay"
    @mouseleave="resumeAutoPlay"
  >
    <div v-if="banners && banners.length > 0" class="banner-content">
      <!-- 轮播幻灯片 -->
      <div class="banner-slides">
        <div
          v-for="(banner, index) in banners"
          :key="banner.video_id"
          class="banner-slide"
          :class="{ 'active': currentIndex === index }"
        >
          <div class="banner-image-container">
            <img
              :src="banner.cover_url"
              :alt="banner.title"
              class="banner-image"
              :class="{ 'blurred': shouldBlur && blurMode === 'blur' }"
              loading="lazy"
              referrerpolicy="no-referrer"
            />
            <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
            <div v-if="shouldBlur && blurMode === 'hide'" class="hide-overlay">
              <el-icon :size="64" class="hide-icon"><Hide /></el-icon>
              <span class="hide-text">图片已隐藏</span>
            </div>
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
      </div>

      <!-- 左右导航箭头 -->
      <button class="nav-arrow nav-arrow-left" @click.stop="prev" :aria-label="'上一个'">
        <el-icon :size="28"><ArrowLeft /></el-icon>
      </button>
      <button class="nav-arrow nav-arrow-right" @click.stop="next" :aria-label="'下一个'">
        <el-icon :size="28"><ArrowRight /></el-icon>
      </button>

      <!-- 圆点指示器 -->
      <div class="dot-indicators" v-if="banners.length > 1">
        <span
          v-for="(_, index) in banners"
          :key="index"
          class="dot"
          :class="{ 'active': currentIndex === index }"
          @click.stop="goTo(index)"
        ></span>
      </div>
    </div>
    <!-- 骨架屏 -->
    <div v-else class="banner-skeleton">
      <el-skeleton-item variant="image" style="width: 100%; height: 100%;" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, onMounted, onUnmounted, watch } from 'vue';
import { BannerVideo } from '../types/video';
import { useRouter } from 'vue-router';
import { useContentSettings } from '../composables/useContentSettings';
import { Hide, ArrowLeft, ArrowRight } from '@element-plus/icons-vue';

export default defineComponent({
  name: 'BannerSlider',
  components: {
    Hide,
    ArrowLeft,
    ArrowRight,
  },
  props: {
    banners: {
      type: Array as PropType<BannerVideo[]>,
      required: true,
      default: () => [],
    },
    isRefreshing: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['refresh'],
  setup(props) {
    const router = useRouter();
    const { shouldBlur, mode } = useContentSettings();

    const currentIndex = ref(0);
    let autoPlayTimer: ReturnType<typeof setInterval> | null = null;
    const INTERVAL = 5000;

    const startAutoPlay = () => {
      stopAutoPlay();
      if (props.banners.length > 1) {
        autoPlayTimer = setInterval(() => {
          currentIndex.value = (currentIndex.value + 1) % props.banners.length;
        }, INTERVAL);
      }
    };

    const stopAutoPlay = () => {
      if (autoPlayTimer) {
        clearInterval(autoPlayTimer);
        autoPlayTimer = null;
      }
    };

    const pauseAutoPlay = () => {
      stopAutoPlay();
    };

    const resumeAutoPlay = () => {
      startAutoPlay();
    };

    const prev = () => {
      currentIndex.value = (currentIndex.value - 1 + props.banners.length) % props.banners.length;
    };

    const next = () => {
      currentIndex.value = (currentIndex.value + 1) % props.banners.length;
    };

    const goTo = (index: number) => {
      currentIndex.value = index;
    };

    const handleBannerClick = (videoId: string) => {
      router.push(`/video/${videoId}`);
    };

    // banners 变化时重置索引并重启自动播放
    watch(() => props.banners, (newVal) => {
      if (currentIndex.value >= newVal.length) {
        currentIndex.value = 0;
      }
      startAutoPlay();
    });

    onMounted(() => {
      startAutoPlay();
    });

    onUnmounted(() => {
      stopAutoPlay();
    });

    return {
      currentIndex,
      handleBannerClick,
      shouldBlur,
      blurMode: mode,
      pauseAutoPlay,
      resumeAutoPlay,
      prev,
      next,
      goTo,
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
  background-color: var(--bg-secondary-color);
}

/* 轮播幻灯片容器 */
.banner-slides {
  position: relative;
  width: 100%;
  height: 100%;
}

.banner-slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 0.6s ease-in-out;
  z-index: 1;
}

.banner-slide.active {
  opacity: 1;
  z-index: 2;
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

.banner-image.blurred {
  filter: blur(20px) brightness(0.8);
  transform: scale(1.1);
}

.banner-image-container .blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
}

.banner-image-container .hide-overlay {
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
}

.banner-image-container .hide-icon {
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 12px;
}

.banner-image-container .hide-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 16px;
  font-weight: 500;
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

/* 导航箭头 */
.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.3s ease;
  backdrop-filter: blur(4px);
}

.banner-container:hover .nav-arrow {
  opacity: 1;
}

.nav-arrow:hover {
  background: rgba(236, 72, 153, 0.7);
  transform: translateY(-50%) scale(1.08);
}

.nav-arrow:active {
  transform: translateY(-50%) scale(0.95);
}

.nav-arrow-left {
  left: 12px;
}

.nav-arrow-right {
  right: 12px;
}

/* 圆点指示器 */
.dot-indicators {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 20px;
  backdrop-filter: blur(4px);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
}

.dot:hover {
  background: rgba(255, 255, 255, 0.7);
}

.dot.active {
  background: #ec4899;
  box-shadow: 0 0 6px rgba(236, 72, 153, 0.6);
  transform: scale(1.2);
}

.banner-skeleton {
  width: 100%;
  height: 380px;
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--bg-secondary-color);
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

  .nav-arrow {
    width: 36px;
    height: 36px;
  }

  .nav-arrow-left {
    left: 8px;
  }

  .nav-arrow-right {
    right: 8px;
  }

  .dot-indicators {
    bottom: 8px;
    gap: 6px;
    padding: 5px 10px;
  }

  .dot {
    width: 8px;
    height: 8px;
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

  .nav-arrow {
    width: 32px;
    height: 32px;
    opacity: 0.7;
  }

  .nav-arrow-left {
    left: 4px;
  }

  .nav-arrow-right {
    right: 4px;
  }

  .dot-indicators {
    bottom: 6px;
    gap: 5px;
    padding: 4px 8px;
  }

  .dot {
    width: 7px;
    height: 7px;
  }

  .banner-skeleton {
    height: 200px;
  }
}
</style>
