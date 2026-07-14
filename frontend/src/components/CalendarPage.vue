<template>
  <div class="page-container">
    <h2 class="page-title">新番列表</h2>

    <!-- 骨架屏 -->
    <template v-if="isLoading">
      <div class="calendar-skeleton" v-for="i in 5" :key="'csk-'+i">
        <div class="skeleton-genre-header">
          <el-skeleton-item variant="text" style="width: 100px; height: 24px;" />
        </div>
        <div class="skeleton-videos">
          <div class="skeleton-video-item" v-for="j in 3" :key="'sv-'+j">
            <el-skeleton-item variant="image" style="width: 160px; height: 90px;" />
            <div class="skeleton-video-text">
              <el-skeleton-item variant="text" style="width: 140px;" />
              <el-skeleton-item variant="text" style="width: 80px;" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 新番内容 -->
    <template v-if="!isLoading">
      <div v-if="calendarData.error" class="error-msg">
        <p>{{ calendarData.error }}</p>
      </div>

      <div v-else-if="calendarData.days.length === 0" class="empty-msg">
        <p>暂无新番数据</p>
      </div>

      <div v-else class="calendar-days">
        <div
          v-for="(day, index) in calendarData.days"
          :key="index"
          class="genre-section"
        >
          <div class="genre-header" @click="toggleSection(index)">
            <div class="genre-info">
              <span class="genre-name">{{ day.day_of_week }}</span>
            </div>
            <span class="genre-count">{{ day.videos.length }}部</span>
            <svg class="toggle-icon" :class="{ expanded: expandedSections[index] }" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <div class="genre-videos" v-show="expandedSections[index]">
            <div v-if="day.videos.length === 0" class="no-videos">暂无番剧</div>
            <div
              v-for="video in day.videos"
              :key="video.video_id"
              class="video-item"
              @click="goToVideo(video.video_id)"
            >
              <div class="video-thumb portrait">
                <img :src="video.cover_url" :alt="video.title" loading="lazy" referrerpolicy="no-referrer" />
              </div>
              <div class="video-info">
                <div class="video-title">{{ video.title }}</div>
                <div class="video-meta">
                  <span v-if="video.duration" class="meta-item">{{ video.duration }}</span>
                  <span v-if="video.like_rate" class="meta-item">{{ video.like_rate }}</span>
                </div>
                <div v-if="video.studio" class="video-studio">{{ video.studio.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <el-backtop :right="20" :bottom="20"></el-backtop>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { VideoApi } from '../api/video';
import { CalendarData } from '../types/video';

export default defineComponent({
  name: 'CalendarPage',
  setup() {
    const router = useRouter();
    const isLoading = ref(true);
    const calendarData = ref<CalendarData>({ days: [] });
    const expandedSections = reactive<Record<number, boolean>>({});

    const fetchCalendarData = async () => {
      isLoading.value = true;
      try {
        calendarData.value = await VideoApi.getCalendarData();
        // 默认展开所有分类
        calendarData.value.days.forEach((_, index) => {
          expandedSections[index] = true;
        });
      } finally {
        isLoading.value = false;
      }
    };

    const toggleSection = (index: number) => {
      expandedSections[index] = !expandedSections[index];
    };

    const goToVideo = (videoId: string) => {
      router.push(`/video/${videoId}`);
    };

    onMounted(fetchCalendarData);

    return {
      isLoading,
      calendarData,
      expandedSections,
      toggleSection,
      goToVideo,
    };
  },
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px;
  background-color: #18181b;
  min-height: 100vh;
  color: #fff;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 20px 0;
  padding-left: 12px;
  border-left: 4px solid #ec4899;
  color: var(--text-color);
}

.error-msg, .empty-msg {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary-color);
  font-size: 16px;
}

/* 分类区块 */
.genre-section {
  margin-bottom: 12px;
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.genre-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid var(--border-color);
  user-select: none;
}

.genre-header:hover {
  background-color: rgba(255, 255, 255, 0.04);
}

.genre-info {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.genre-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.genre-count {
  font-size: 13px;
  color: #ec4899;
  margin-right: 8px;
}

.toggle-icon {
  transition: transform 0.25s;
  color: var(--text-secondary-color);
  flex-shrink: 0;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

/* 视频网格列表 */
.genre-videos {
  padding: 12px;
}

.no-videos {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary-color);
  font-size: 14px;
}

.video-item {
  display: inline-block;
  width: calc(16.666% - 12px);
  margin: 6px;
  vertical-align: top;
  cursor: pointer;
  transition: transform 0.2s;
}

.video-item:hover {
  transform: translateY(-3px);
}

.video-thumb {
  width: 100%;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.video-thumb.portrait {
  padding-top: 142%;
}

.video-thumb.portrait img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-info {
  padding: 6px 2px;
}

.video-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  margin-bottom: 2px;
}

.video-meta {
  display: flex;
  gap: 8px;
}

.meta-item {
  font-size: 11px;
  color: var(--text-secondary-color);
}

.video-studio {
  font-size: 11px;
  color: #ec4899;
  opacity: 0.8;
}

/* 骨架屏 */
.calendar-skeleton {
  margin-bottom: 12px;
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  padding: 12px 16px;
}

.skeleton-genre-header {
  margin-bottom: 12px;
}

.skeleton-videos {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-video-item {
  display: flex;
  gap: 12px;
  align-items: center;
}

.skeleton-video-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .video-item {
    width: calc(20% - 12px);
  }
}

@media (max-width: 992px) {
  .video-item {
    width: calc(25% - 12px);
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 8px;
  }

  .video-item {
    width: calc(33.333% - 10px);
    margin: 5px;
  }

  .video-title {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .page-container {
    padding: 5px;
  }

  .page-title {
    font-size: 18px;
    margin-bottom: 12px;
  }

  .genre-header {
    padding: 10px 12px;
  }

  .genre-name {
    font-size: 14px;
  }

  .video-item {
    width: calc(50% - 8px);
    margin: 4px;
  }

  .video-title {
    font-size: 11px;
  }
}
</style>
