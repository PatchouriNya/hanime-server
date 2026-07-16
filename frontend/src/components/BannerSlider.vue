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
              :class="{ 'blurred': shouldBlur && blurMode === 'blur', 'ken-burns': currentIndex === index }"
              loading="lazy"
              referrerpolicy="no-referrer"
            />
            <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
            <div v-if="shouldBlur && blurMode === 'hide'" class="hide-overlay">
              <el-icon :size="64" class="hide-icon"><Hide /></el-icon>
              <span class="hide-text">图片已隐藏</span>
            </div>
            <!-- 多层渐变遮罩 -->
            <div class="banner-gradient-dark"></div>
            <div class="banner-gradient-accent"></div>
            <div class="banner-gradient-vignette"></div>
          </div>
        </div>
      </div>

      <!-- 左右导航箭头 -->
      <button class="nav-arrow nav-arrow-left" @click.stop="prev" :aria-label="'上一个'">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </button>
      <button class="nav-arrow nav-arrow-right" @click.stop="next" :aria-label="'下一个'">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
      </button>

      <!-- 底部信息面板 -->
      <div class="banner-bottom-panel">
        <div class="banner-text-area">
          <h2 class="banner-title">{{ currentBanner?.title }}</h2>
          <p v-if="currentBanner?.description" class="banner-description">{{ currentBanner.description }}</p>
        </div>
        <div class="banner-action-area">
          <button class="play-glow-btn" @click.stop="handleBannerClick(currentBanner?.video_id)">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <span>播放</span>
          </button>
          <button class="refresh-glow-btn" :class="{ spinning: isRefreshing }" @click.stop="$emit('refresh')" title="刷新推荐">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          </button>
        </div>
      </div>

      <!-- 胶囊指示器 -->
      <div class="capsule-indicators" v-if="banners.length > 1">
        <span
          v-for="(_, index) in banners"
          :key="index"
          class="capsule"
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
import { defineComponent, PropType, ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { BannerVideo } from '../types/video';
import { useRouter } from 'vue-router';
import { useContentSettings } from '../composables/useContentSettings';
import { Hide } from '@element-plus/icons-vue';

export default defineComponent({
  name: 'BannerSlider',
  components: { Hide },
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

    const currentBanner = computed(() => props.banners[currentIndex.value]);

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

    const pauseAutoPlay = () => stopAutoPlay();
    const resumeAutoPlay = () => startAutoPlay();

    const prev = () => {
      currentIndex.value = (currentIndex.value - 1 + props.banners.length) % props.banners.length;
    };
    const next = () => {
      currentIndex.value = (currentIndex.value + 1) % props.banners.length;
    };
    const goTo = (index: number) => {
      currentIndex.value = index;
    };
    const handleBannerClick = (videoId?: string) => {
      if (videoId) router.push(`/video/${videoId}`);
    };

    watch(() => props.banners, (newVal) => {
      if (currentIndex.value >= newVal.length) currentIndex.value = 0;
      startAutoPlay();
    });

    onMounted(() => startAutoPlay());
    onUnmounted(() => stopAutoPlay());

    return {
      currentIndex, currentBanner, handleBannerClick,
      shouldBlur, blurMode: mode,
      pauseAutoPlay, resumeAutoPlay, prev, next, goTo,
    };
  },
});
</script>

<style scoped>
.banner-container {
  width: 100%;
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.banner-content {
  position: relative;
  height: 420px;
  background-color: #0a0a0a;
}

.banner-slides {
  position: relative;
  width: 100%;
  height: 100%;
}

.banner-slide {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  opacity: 0;
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}
.banner-slide.active { opacity: 1; z-index: 2; }

.banner-image-container {
  position: relative;
  width: 100%;
  height: 420px;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: none;
}

/* Ken Burns 微缩放动画 */
.banner-image.ken-burns {
  animation: kenBurns 8s ease-out forwards;
}

@keyframes kenBurns {
  0% { transform: scale(1); }
  100% { transform: scale(1.06); }
}

.banner-image.blurred {
  filter: blur(20px) brightness(0.8);
  transform: scale(1.1);
}

.banner-image-container .blur-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 3;
}

.banner-image-container .hide-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%);
  z-index: 3;
}
.banner-image-container .hide-icon { color: rgba(255,255,255,0.4); margin-bottom: 12px; }
.banner-image-container .hide-text { color: rgba(255,255,255,0.4); font-size: 16px; }

/* 多层渐变遮罩 - 电影感 */
.banner-gradient-dark {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.95) 0%,
    rgba(0, 0, 0, 0.7) 25%,
    rgba(0, 0, 0, 0.2) 55%,
    transparent 100%
  );
  z-index: 4;
}

.banner-gradient-accent {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.6) 0%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(236, 72, 153, 0.08) 100%
  );
  z-index: 4;
}

.banner-gradient-vignette {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(
    ellipse at center,
    transparent 50%,
    rgba(0, 0, 0, 0.4) 100%
  );
  z-index: 4;
}

/* 底部信息面板 - 毛玻璃 */
.banner-bottom-panel {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 40px 24px 28px;
  background: linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.7) 0%,
    transparent 100%
  );
}

.banner-text-area {
  flex: 1;
  margin-right: 20px;
  max-width: 70%;
}

.banner-title {
  margin: 0 0 8px;
  font-size: 28px;
  color: #fff;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
  letter-spacing: 0.3px;
}

.banner-description {
  margin: 0;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.banner-action-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* 发光播放按钮 */
.play-glow-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 24px;
  background: linear-gradient(135deg, #ec4899, #f43f5e);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.4);
  letter-spacing: 0.5px;
}
.play-glow-btn:hover {
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 6px 24px rgba(236, 72, 153, 0.6);
}
.play-glow-btn:active {
  transform: translateY(0) scale(0.98);
}

/* 刷新按钮 */
.refresh-glow-btn {
  width: 40px; height: 40px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.25s;
}
.refresh-glow-btn:hover {
  background: rgba(236, 72, 153, 0.3);
  border-color: #ec4899;
  color: #ec4899;
  transform: scale(1.08);
}
.refresh-glow-btn.spinning { pointer-events: none; opacity: 0.5; }
.refresh-glow-btn.spinning svg { animation: spin 1s linear infinite; }

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
  width: 44px; height: 44px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.3s ease;
}
.banner-container:hover .nav-arrow { opacity: 1; }
.nav-arrow:hover {
  background: rgba(236, 72, 153, 0.6);
  transform: translateY(-50%) scale(1.08);
}
.nav-arrow:active { transform: translateY(-50%) scale(0.95); }
.nav-arrow-left { left: 14px; }
.nav-arrow-right { right: 14px; }

/* 胶囊指示器 */
.capsule-indicators {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 20px;
  backdrop-filter: blur(8px);
}
.capsule {
  width: 8px; height: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.35);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.capsule:hover { background: rgba(255, 255, 255, 0.6); }
.capsule.active {
  width: 24px;
  background: #ec4899;
  box-shadow: 0 0 8px rgba(236, 72, 153, 0.5);
}

.banner-skeleton {
  width: 100%; height: 420px;
  border-radius: 16px;
  overflow: hidden;
  background-color: var(--bg-secondary-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .banner-content, .banner-image-container { height: 300px; }
  .banner-skeleton { height: 300px; }
  .banner-bottom-panel { padding: 30px 16px 20px; }
  .banner-title { font-size: 22px; }
  .banner-description { font-size: 13px; }
  .play-glow-btn { padding: 8px 18px; font-size: 13px; }
  .nav-arrow { width: 38px; height: 38px; }
  .nav-arrow-left { left: 8px; }
  .nav-arrow-right { right: 8px; }
}

@media (max-width: 480px) {
  .banner-content, .banner-image-container { height: 220px; }
  .banner-skeleton { height: 220px; }
  .banner-bottom-panel { padding: 20px 12px 14px; }
  .banner-title { font-size: 17px; margin-bottom: 4px; }
  .banner-description { font-size: 12px; -webkit-line-clamp: 1; }
  .banner-text-area { max-width: 60%; }
  .play-glow-btn { padding: 7px 14px; font-size: 12px; gap: 5px; }
  .play-glow-btn svg { width: 16px; height: 16px; }
  .refresh-glow-btn { width: 34px; height: 34px; }
  .nav-arrow { width: 32px; height: 32px; opacity: 0.6; }
  .nav-arrow-left { left: 4px; }
  .nav-arrow-right { right: 4px; }
  .capsule-indicators { bottom: 8px; gap: 4px; padding: 4px 8px; }
  .capsule { width: 6px; height: 6px; }
  .capsule.active { width: 18px; }
  .banner-container { border-radius: 10px; margin-bottom: 16px; }
}
</style>
