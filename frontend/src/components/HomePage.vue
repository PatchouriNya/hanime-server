<template>
  <div class="page-container">
    <!-- Banner区域 -->
    <banner-slider :banners="homeData.banners" :is-refreshing="isRefreshing" @refresh="handleRefresh"/>

    <!-- 骨架屏 - 加载中 -->
    <template v-if="isLoading">
      <div class="skeleton-section" v-for="i in 3" :key="'sk-'+i">
        <div class="skeleton-header">
          <el-skeleton-item variant="text" style="width: 120px; height: 22px;" />
          <el-skeleton-item variant="text" style="width: 70px; height: 28px;" />
        </div>
        <div class="skeleton-cards">
          <div class="skeleton-card" v-for="j in 6" :key="'skc-'+j">
            <el-skeleton-item variant="image" style="width: 100%; height: 0; padding-top: 142%;" />
            <el-skeleton-item variant="text" style="margin-top: 8px; width: 80%;" />
          </div>
        </div>
      </div>
    </template>

    <!-- 视频区块通用组件 -->
    <template v-if="!isLoading" v-for="(section, index) in homeData.latest_videos" :key="`latest-${index}`">
      <video-section
        :title="section.title"
        :search-suffix="section.search_suffix"
        :videos="section.videos"
        item-class="latest-horizontal-item"
        thumbnail-class="portrait"
        @view-more="handleViewMore"
        @video-click="handleVideoClick"
      />
    </template>

    <!-- 其他视频分类 -->
    <template v-if="!isLoading" v-for="(section, key) in filteredVideoSections" :key="key">
      <video-section 
        v-if="section[0]?.videos?.length"
        :title="section[0].title" 
        :search-suffix="section[0].search_suffix" 
        :videos="section[0].videos"
        thumbnail-class="landscape" 
        @view-more="handleViewMore"
        @video-click="handleVideoClick"
      />
    </template>

    <!-- 返回顶部按钮 -->
    <el-backtop :right="20" :bottom="20"></el-backtop>
  </div>
</template>

<script lang="ts">
import {computed, defineComponent, onMounted, onUnmounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import {VideoApi} from '../api/video';
import {HomeData} from '../types/video';
import BannerSlider from '../components/BannerSlider.vue';
import VideoSection from '../components/VideoSection.vue';
import {mitt} from '../utils/mitt';

export default defineComponent({
  name: 'HomePage',
  components: {
    BannerSlider,
    VideoSection
  },
  setup() {
    const router = useRouter();
    const isRefreshing = ref(false);
    const isLoading = ref(true);
    const homeData = ref<HomeData>({
      banners: [],
      latest_videos: [],
      new_arrivals_videos: [],
      new_uploads_videos: [],
      popular_videos: [],
      ai_generated_videos: [],
      bubble_tea_videos: [],
      daily_rank_videos: [],
      monthly_rank_videos: [],
    });

    const filteredVideoSections = computed(() => ({
      new_arrivals: homeData.value.new_arrivals_videos,
      new_uploads: homeData.value.new_uploads_videos,
      popular: homeData.value.popular_videos,
      daily_rank: homeData.value.daily_rank_videos,
      monthly_rank: homeData.value.monthly_rank_videos,
      ai_generated: homeData.value.ai_generated_videos,
      bubble_tea: homeData.value.bubble_tea_videos
    }));

    const fetchHomeData = async () => {
      isLoading.value = true;
      try {
        homeData.value = await VideoApi.getHomeData();
      } finally {
        isLoading.value = false;
      }
    };

    const handleRefresh = async () => {
      if (isRefreshing.value) return;
      isRefreshing.value = true;
      try {
        homeData.value = await VideoApi.refreshHomeData();
      } finally {
        isRefreshing.value = false;
      }
    };

    const handleVideoClick = (videoId: string) => {
      router.push(`/video/${videoId}`);
    };

    const handleViewMore = (searchSuffix: string) => {
      if (!searchSuffix) return;
      // 解析 search_suffix 为搜索页面可识别的 query 参数
      const params = new URLSearchParams(searchSuffix);
      const query: Record<string, any> = {};
      const tags: string[] = [];

      params.forEach((value, key) => {
        if (key === 'tags[]' || key === 'tags') {
          tags.push(value);
        } else {
          query[key] = value;
        }
      });

      if (tags.length > 0) {
        query.tags = tags;
      }

      router.push({ path: '/search', query });
    };

    // 监听来自 AppHeader 的刷新事件
    const onRefreshFromHeader = () => {
      handleRefresh();
    };
    mitt.on('refresh-home', onRefreshFromHeader);

    onMounted(fetchHomeData);

    onUnmounted(() => {
      mitt.off('refresh-home', onRefreshFromHeader);
    });

    return {
      homeData,
      filteredVideoSections,
      fetchHomeData,
      handleRefresh,
      isRefreshing,
      isLoading,
      handleVideoClick,
      handleViewMore,
    };
  },
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  background-color: var(--bg-color);
  min-height: 100vh;
  color: var(--text-color);
  overflow-x: hidden;
}

/* 骨架屏样式 */
.skeleton-section {
  margin-bottom: 24px;
  background-color: var(--bg-secondary-color);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 12px;
}

.skeleton-cards {
  display: flex;
  gap: 14px;
  overflow: hidden;
}

.skeleton-card {
  flex: 0 0 160px;
}

/* PC端大气布局 */
@media (min-width: 769px) {
  .page-container {
    max-width: 1400px;
    padding: 24px 32px;
  }

  .skeleton-section {
    padding: 24px;
    margin-bottom: 28px;
  }

  .skeleton-header {
    margin-bottom: 20px;
    padding-bottom: 14px;
  }

  .skeleton-card {
    flex: 0 0 180px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 10px;
  }
  .skeleton-card {
    flex: 0 0 140px;
  }
}

@media (max-width: 480px) {
  .page-container {
    padding: 6px;
  }
  .skeleton-card {
    flex: 0 0 120px;
  }
}
</style> 