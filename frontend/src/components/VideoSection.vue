<template>
  <div class="video-section">
    <div class="section-header">
      <h2 class="section-title">{{ title }}</h2>
      <el-button
          v-if="searchSuffix"
          type="primary"
          size="small"
          @click="$emit('view-more', searchSuffix)"
          class="more-btn"
      >
        查看更多
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <div class="scroll-wrapper">
      <button
        v-if="showLeftArrow"
        class="scroll-arrow scroll-arrow-left"
        @click="scrollByPage('left')"
        @mouseenter="startAutoScroll('left')"
        @mouseleave="stopAutoScroll"
      >
        <el-icon :size="20"><ArrowLeft /></el-icon>
      </button>

      <div class="horizontal-scroll" ref="scrollContainerRef" @scroll="updateArrowVisibility">
        <video-card
            v-for="(video, index) in videos"
            :key="video.video_id"
            :video="video"
            :thumbnail-class="thumbnailClass"
            :custom-class="'horizontal-item ' + itemClass"
            :single-line-title="thumbnailClass === 'landscape'"
            :style="{ animationDelay: `${index * 50}ms` }"
            @click="(videoId) => $emit('video-click', videoId)"
        />
      </div>

      <button
        v-if="showRightArrow"
        class="scroll-arrow scroll-arrow-right"
        @click="scrollByPage('right')"
        @mouseenter="startAutoScroll('right')"
        @mouseleave="stopAutoScroll"
      >
        <el-icon :size="20"><ArrowRight /></el-icon>
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import {defineComponent, PropType, ref, onMounted, onUnmounted, nextTick} from 'vue';
import {VideoBase, VideoPreview} from '../types/video';
import VideoCard from "./VideoCard.vue";
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue';

export default defineComponent({
  name: 'VideoSection',
  components: {
    VideoCard,
    ArrowLeft,
    ArrowRight
  },
  props: {
    title: {
      type: String,
      required: true
    },
    searchSuffix: {
      type: String,
      default: ''
    },
    videos: {
      type: Array as PropType<(VideoBase | VideoPreview)[]>,
      required: true
    },
    itemClass: {
      type: String,
      default: ''
    },
    thumbnailClass: {
      type: String,
      default: 'landscape'
    }
  },
  emits: ['view-more', 'video-click'],
  setup() {
    const scrollContainerRef = ref<HTMLElement | null>(null);
    const showLeftArrow = ref(false);
    const showRightArrow = ref(false);
    let autoScrollTimer: ReturnType<typeof setInterval> | null = null;
    let isMobile = window.innerWidth <= 768;

    const updateArrowVisibility = () => {
      const el = scrollContainerRef.value;
      if (!el || isMobile) {
        showLeftArrow.value = false;
        showRightArrow.value = false;
        return;
      }
      showLeftArrow.value = el.scrollLeft > 10;
      showRightArrow.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 10;
    };

    const scrollByPage = (direction: 'left' | 'right') => {
      stopAutoScroll();
      const el = scrollContainerRef.value;
      if (!el) return;
      const scrollAmount = el.clientWidth * 0.8;
      el.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    };

    const startAutoScroll = (direction: 'left' | 'right') => {
      stopAutoScroll();
      const el = scrollContainerRef.value;
      if (!el) return;
      autoScrollTimer = setInterval(() => {
        el.scrollBy({ left: direction === 'left' ? -6 : 6 });
      }, 16);
    };

    const stopAutoScroll = () => {
      if (autoScrollTimer) {
        clearInterval(autoScrollTimer);
        autoScrollTimer = null;
      }
    };

    const handleResize = () => {
      isMobile = window.innerWidth <= 768;
      updateArrowVisibility();
    };

    onMounted(() => {
      nextTick(() => {
        updateArrowVisibility();
      });
      window.addEventListener('resize', handleResize);
    });

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize);
      stopAutoScroll();
    });

    return {
      scrollContainerRef,
      showLeftArrow,
      showRightArrow,
      updateArrowVisibility,
      scrollByPage,
      startAutoScroll,
      stopAutoScroll
    };
  }
});
</script>

<style scoped>
.video-section {
  margin-bottom: 24px;
  background-color: var(--bg-secondary-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: box-shadow 0.3s ease;
}

.video-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  position: relative;
  padding-left: 14px;
  letter-spacing: 0.3px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 20px;
  width: 4px;
  background: linear-gradient(180deg, #ec4899, #f43f5e);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(236, 72, 153, 0.4);
}

.more-btn {
  font-weight: 500;
  transition: all 0.3s;
  background: linear-gradient(135deg, #ec4899, #f43f5e);
  border-color: transparent;
  border-radius: 20px;
  padding: 6px 16px;
}

.more-btn:hover {
  background: linear-gradient(135deg, #d946ef, #e11d48);
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);
}

.more-btn i {
  margin-left: 5px;
  transition: transform 0.3s;
}

.more-btn:hover i {
  transform: translateX(3px);
}

/* Scroll wrapper with arrows */
.scroll-wrapper {
  position: relative;
}

.horizontal-scroll {
  display: flex;
  overflow-x: auto;
  gap: 14px;
  padding-bottom: 8px;
  scroll-behavior: smooth;
}

/* Desktop: hide scrollbar, show arrows */
@media (min-width: 769px) {
  .horizontal-scroll {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .horizontal-scroll::-webkit-scrollbar {
    display: none;
  }
}

/* Mobile: show thin scrollbar */
@media (max-width: 768px) {
  .horizontal-scroll {
    scrollbar-width: thin;
  }

  .horizontal-scroll::-webkit-scrollbar {
    height: 4px;
  }

  .horizontal-scroll::-webkit-scrollbar-track {
    background: transparent;
  }

  .horizontal-scroll::-webkit-scrollbar-thumb {
    background: rgba(236, 72, 153, 0.2);
    border-radius: 10px;
  }
}

/* Arrow buttons - vertical bar style */
.scroll-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 32px;
  height: 80px;
  border-radius: 6px;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.scroll-arrow:hover {
  background: rgba(236, 72, 153, 0.85);
  width: 36px;
}

.scroll-arrow-left {
  left: 2px;
}

.scroll-arrow-right {
  right: 2px;
}

/* Hide arrows on mobile */
@media (max-width: 768px) {
  .scroll-arrow {
    display: none !important;
  }
}

.horizontal-item {
  flex: 0 0 240px;
}

.latest-horizontal-item {
  flex: 0 0 160px;
}

/* Light theme adjustments */
:global(.light) .scroll-arrow {
  background: rgba(255, 255, 255, 0.9);
  color: var(--text-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:global(.light) .scroll-arrow:hover {
  background: var(--primary-color);
  color: #fff;
}

/* Responsive */
@media (max-width: 768px) {
  .video-section {
    padding: 14px;
    margin-bottom: 16px;
    border-radius: 10px;
  }

  .section-title {
    font-size: 16px;
  }

  .horizontal-item {
    flex: 0 0 180px;
  }

  .latest-horizontal-item {
    flex: 0 0 140px;
  }
}

@media (max-width: 480px) {
  .video-section {
    padding: 10px;
    margin-bottom: 12px;
  }

  .section-title {
    font-size: 14px;
    padding-left: 10px;
  }

  .section-title::before {
    height: 16px;
    width: 3px;
  }

  .horizontal-scroll {
    gap: 8px;
  }

  .horizontal-item {
    flex: 0 0 45%;
  }

  .latest-horizontal-item {
    flex: 0 0 32%;
  }

  .more-btn {
    font-size: 12px;
    padding: 5px 12px;
  }
}
</style>
