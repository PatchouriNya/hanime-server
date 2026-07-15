<template>
  <div class="calendar-page">
    <!-- 顶部渐变装饰线 -->
    <div class="header-gradient-bar"></div>

    <!-- 头部区域 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="header-text">
          <h1 class="header-title">新番列表</h1>
          <p class="header-subtitle" v-if="!isLoading && totalVideoCount > 0">
            共 {{ totalVideoCount }} 部新番更新
          </p>
        </div>
      </div>
    </div>

    <!-- 类型标签过滤 -->
    <div class="genre-filter" v-if="!isLoading && calendarData.days.length > 0">
      <div class="filter-scroll">
        <button
          class="filter-tab"
          :class="{ active: activeFilter === 'all' }"
          @click="activeFilter = 'all'"
        >
          <span class="tab-text">全部</span>
          <span class="tab-count">{{ totalVideoCount }}</span>
        </button>
        <button
          v-for="day in calendarData.days"
          :key="day.day_of_week"
          class="filter-tab"
          :class="{ active: activeFilter === day.day_of_week }"
          @click="activeFilter = day.day_of_week"
        >
          <span class="tab-text">{{ day.day_of_week }}</span>
          <span class="tab-count">{{ day.videos.length }}</span>
        </button>
      </div>
    </div>

    <!-- 骨架屏 -->
    <template v-if="isLoading">
      <div class="calendar-skeleton" v-for="i in 3" :key="'csk-'+i">
        <div class="skeleton-section-header">
          <el-skeleton-item variant="text" style="width: 80px; height: 20px;" />
          <el-skeleton-item variant="text" style="width: 30px; height: 18px;" />
        </div>
        <div class="skeleton-grid">
          <div class="skeleton-card" v-for="j in 5" :key="'sv-'+j">
            <el-skeleton-item variant="image" style="width: 100%; height: 0; padding-top: 142%; border-radius: 8px;" />
            <div class="skeleton-card-text">
              <el-skeleton-item variant="text" style="width: 90%;" />
              <el-skeleton-item variant="text" style="width: 60%;" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 内容区域 -->
    <template v-if="!isLoading">
      <!-- 错误状态 -->
      <div v-if="calendarData.error" class="state-container">
        <div class="state-icon">
          <svg viewBox="0 0 24 24" width="56" height="56" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <p class="state-text">{{ calendarData.error }}</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="calendarData.days.length === 0 || filteredDays.length === 0" class="state-container">
        <div class="state-icon">
          <svg viewBox="0 0 24 24" width="56" height="56" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
            <line x1="9" y1="16" x2="15" y2="16"></line>
          </svg>
        </div>
        <p class="state-text">暂无新番数据</p>
        <p class="state-subtext">新番更新后将在这里显示</p>
      </div>

      <!-- 新番列表 -->
      <div v-else class="genre-list">
        <div
          v-for="(day, index) in filteredDays"
          :key="day.day_of_week"
          class="genre-section"
        >
          <!-- 分类头部 -->
          <div class="section-header" @click="toggleSection(day.day_of_week)">
            <div class="accent-bar" :style="{ backgroundColor: getAccentColor(index) }"></div>
            <span class="section-name">{{ day.day_of_week }}</span>
            <span class="section-count-badge" :style="{ backgroundColor: getAccentColor(index) }">
              {{ day.videos.length }}
            </span>
            <svg
              class="toggle-chevron"
              :class="{ expanded: expandedSections[day.day_of_week] }"
              viewBox="0 0 24 24"
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <!-- 视频网格 -->
          <transition name="section-expand">
            <div
              v-if="expandedSections[day.day_of_week]"
              class="section-content"
            >
              <div class="video-grid">
                <div
                  v-for="video in day.videos"
                  :key="video.video_id"
                  class="video-card"
                  @click="goToVideo(video.video_id)"
                >
                  <!-- 封面图 -->
                  <div
                    class="card-thumbnail portrait"
                    :class="{
                      'blur-cover': shouldBlur && blurMode === 'blur',
                      'hide-cover': shouldBlur && blurMode === 'hide'
                    }"
                  >
                    <img
                      :src="video.cover_url"
                      :alt="video.title"
                      loading="lazy"
                      referrerpolicy="no-referrer"
                      :class="{ 'blurred': shouldBlur && blurMode === 'blur' }"
                    />
                    <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
                    <div v-if="shouldBlur && blurMode === 'hide'" class="hide-overlay">
                      <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="hide-icon">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                      <span class="hide-label">已隐藏</span>
                    </div>
                    <!-- 时长徽章 -->
                    <span v-if="video.duration" class="badge badge-duration">{{ video.duration }}</span>
                    <!-- 点赞率徽章 -->
                    <span v-if="video.like_rate" class="badge badge-like">
                      <svg viewBox="0 0 1024 1024" width="10" height="10" style="margin-right:2px;vertical-align:middle;">
                        <path d="M885.9 533.7c16.8-22.2 26.1-49.4 26.1-77.7 0-44.9-25.1-87.4-65.5-111.1a67.67 67.67 0 0 0-34.3-9.3H572.4l6-122.9c1.4-29.7-9.1-57.9-29.5-79.4-20.5-21.5-48.1-33.4-77.9-33.4-52 0-98 35-111.8 85.1l-85.9 311H144c-17.7 0-32 14.3-32 32v364c0 17.7 14.3 32 32 32h601.3c9.2 0 18.2-1.8 26.5-5.4 47.6-20.3 78.3-66.8 78.3-118.4 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7-0.2-12.6-2-25.1-5.6-37.1zM184 852V568h81v284h-81z m636.4-353l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 16.5-7.2 32.2-19.6 43l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 16.5-7.2 32.2-19.6 43l-21.9 19 13.9 25.4c4.6 8.4 6.9 17.6 6.9 27.3 0 22.4-13.2 42.6-33.6 51.8H329V564.8l99.5-360.5c5.2-18.9 22.5-32.2 42.2-32.3 7.6 0 15.1 2.2 21.1 6.7 9.9 7.4 15.2 18.6 14.6 30.5l-9.6 198.4h314.4C829 418.5 840 436.9 840 456c0 16.5-7.2 32.1-19.6 43z" fill="currentColor"></path>
                      </svg>
                      {{ video.like_rate }}
                    </span>
                  </div>
                  <!-- 卡片信息 -->
                  <div class="card-info">
                    <h3 class="card-title">{{ video.title }}</h3>
                  </div>
                </div>
              </div>
              <!-- 空视频 -->
              <div v-if="day.videos.length === 0" class="empty-section">
                <p>暂无番剧</p>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </template>

    <el-backtop :right="20" :bottom="20"></el-backtop>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { VideoApi } from '../api/video';
import { CalendarData } from '../types/video';
import { useContentSettings } from '../composables/useContentSettings';

const ACCENT_COLORS = [
  '#ec4899', '#8b5cf6', '#06b6d4', '#f59e0b', '#10b981',
  '#ef4444', '#3b82f6', '#f97316', '#14b8a6', '#a855f7',
];

export default defineComponent({
  name: 'CalendarPage',
  setup() {
    const router = useRouter();
    const isLoading = ref(true);
    const calendarData = ref<CalendarData>({ days: [] });
    const expandedSections = reactive<Record<string, boolean>>({});
    const activeFilter = ref('all');
    const { shouldBlur, mode } = useContentSettings();

    const blurMode = computed(() => mode.value);

    const totalVideoCount = computed(() => {
      return calendarData.value.days.reduce((sum, day) => sum + day.videos.length, 0);
    });

    const filteredDays = computed(() => {
      if (activeFilter.value === 'all') return calendarData.value.days;
      return calendarData.value.days.filter(d => d.day_of_week === activeFilter.value);
    });

    const getAccentColor = (index: number) => {
      return ACCENT_COLORS[index % ACCENT_COLORS.length];
    };

    const fetchCalendarData = async () => {
      isLoading.value = true;
      try {
        calendarData.value = await VideoApi.getCalendarData();
        calendarData.value.days.forEach((day) => {
          expandedSections[day.day_of_week] = true;
        });
      } finally {
        isLoading.value = false;
      }
    };

    const toggleSection = (key: string) => {
      expandedSections[key] = !expandedSections[key];
    };

    const goToVideo = (videoId: string) => {
      router.push(`/video/${videoId}`);
    };

    onMounted(fetchCalendarData);

    return {
      isLoading,
      calendarData,
      expandedSections,
      activeFilter,
      shouldBlur,
      blurMode,
      totalVideoCount,
      filteredDays,
      getAccentColor,
      toggleSection,
      goToVideo,
    };
  },
});
</script>

<style scoped>
/* ===== 页面容器 ===== */
.calendar-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px 40px;
  background-color: var(--bg-color);
  min-height: 100vh;
  color: var(--text-color);
}

/* ===== 顶部渐变装饰线 ===== */
.header-gradient-bar {
  height: 3px;
  background: linear-gradient(90deg, #ec4899, #8b5cf6, #06b6d4, #10b981);
  border-radius: 0 0 3px 3px;
  margin: 0 -16px 24px;
}

/* ===== 头部区域 ===== */
.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.35);
}

.header-title {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
  color: var(--text-color);
  letter-spacing: -0.5px;
}

.header-subtitle {
  font-size: 13px;
  color: var(--text-secondary-color);
  margin: 4px 0 0;
}

/* ===== 类型标签过滤 ===== */
.genre-filter {
  margin-bottom: 24px;
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: var(--bg-color);
  padding: 12px 0;
}

.filter-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.filter-scroll::-webkit-scrollbar {
  display: none;
}

.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 20px;
  border: 1.5px solid var(--border-color);
  background-color: var(--bg-secondary-color);
  color: var(--text-secondary-color);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  outline: none;
}

.filter-tab:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background-color: var(--hover-bg-color);
}

.filter-tab.active {
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 10px rgba(236, 72, 153, 0.3);
}

.tab-count {
  font-size: 11px;
  font-weight: 700;
  background-color: rgba(0, 0, 0, 0.15);
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.filter-tab:not(.active) .tab-count {
  background-color: var(--border-color);
  color: var(--text-secondary-color);
}

/* ===== 分类区块 ===== */
.genre-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.genre-section {
  background-color: var(--card-bg-color);
  border-radius: 16px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.genre-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* ===== 分类头部 ===== */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
}

.section-header:hover {
  background-color: var(--hover-bg-color);
}

.accent-bar {
  width: 4px;
  height: 22px;
  border-radius: 2px;
  flex-shrink: 0;
}

.section-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-color);
  flex: 1;
}

.section-count-badge {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  padding: 2px 10px;
  border-radius: 10px;
  flex-shrink: 0;
}

.toggle-chevron {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-secondary-color);
  flex-shrink: 0;
}

.toggle-chevron.expanded {
  transform: rotate(180deg);
}

/* ===== 展开收起动画 ===== */
.section-expand-enter-active,
.section-expand-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.section-expand-enter-from,
.section-expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.section-expand-enter-to,
.section-expand-leave-from {
  opacity: 1;
  max-height: 3000px;
}

.section-content {
  padding: 0 16px 16px;
}

/* ===== 视频网格 ===== */
.video-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

/* ===== 视频卡片 ===== */
.video-card {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  background-color: var(--card-bg-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.video-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
}

/* ===== 缩略图 ===== */
.card-thumbnail.portrait {
  position: relative;
  width: 100%;
  padding-top: 142%;
  overflow: hidden;
}

.card-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.video-card:hover .card-thumbnail img {
  transform: scale(1.08);
}

.card-thumbnail img.blurred {
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
  margin-bottom: 6px;
}

.hide-label {
  color: var(--text-secondary-color);
  font-size: 11px;
  font-weight: 500;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ===== 徽章 ===== */
.badge {
  position: absolute;
  z-index: 2;
  background-color: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  letter-spacing: 0.3px;
}

.badge-duration {
  bottom: 8px;
  right: 8px;
}

.badge-like {
  bottom: 8px;
  left: 8px;
}

/* ===== 卡片信息 ===== */
.card-info {
  padding: 10px 8px;
}

.card-title {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

/* ===== 空状态 & 错误状态 ===== */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.state-icon {
  color: var(--text-secondary-color);
  opacity: 0.4;
  margin-bottom: 16px;
}

.state-text {
  font-size: 16px;
  color: var(--text-secondary-color);
  margin: 0 0 4px;
}

.state-subtext {
  font-size: 13px;
  color: var(--text-secondary-color);
  opacity: 0.6;
  margin: 0;
}

.empty-section {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary-color);
  font-size: 14px;
}

/* ===== 骨架屏 ===== */
.calendar-skeleton {
  background-color: var(--card-bg-color);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.skeleton-section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.skeleton-card {
  border-radius: 12px;
  overflow: hidden;
}

.skeleton-card-text {
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ===== 响应式布局 ===== */
@media (max-width: 1200px) {
  .video-grid,
  .skeleton-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .video-grid,
  .skeleton-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

@media (max-width: 600px) {
  .calendar-page {
    padding: 0 10px 32px;
  }

  .header-gradient-bar {
    margin: 0 -10px 16px;
  }

  .header-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }

  .header-icon svg {
    width: 24px;
    height: 24px;
  }

  .header-title {
    font-size: 22px;
  }

  .filter-tab {
    padding: 6px 12px;
    font-size: 12px;
  }

  .video-grid,
  .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .section-header {
    padding: 12px 14px;
  }

  .section-name {
    font-size: 14px;
  }

  .card-title {
    font-size: 12px;
  }

  .badge {
    font-size: 10px;
    padding: 1px 4px;
  }

  .card-info {
    padding: 8px 6px;
  }
}
</style>
