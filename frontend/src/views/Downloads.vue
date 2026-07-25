<template>
  <div class="downloads-page">
    <div class="downloads-header">
      <div class="header-top">
        <h1 class="page-title">下载管理</h1>
        
        <!-- 视图切换 + 搜索 -->
        <div class="header-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索番剧..."
            prefix-icon="Search"
            clearable
            size="default"
            class="search-input"
            @input="handleSearch"
            @clear="handleSearch"
          />
          
          <el-button-group class="view-toggle">
            <el-button 
              :type="viewMode === 'list' ? 'primary' : 'default'" 
              @click="viewMode = 'list'"
              size="default"
            >
              <el-icon><List /></el-icon> 列表
            </el-button>
            <el-button 
              :type="viewMode === 'group' ? 'primary' : 'default'" 
              @click="viewMode = 'group'; loadGroups()"
              size="default"
            >
              <el-icon><Grid /></el-icon> 番剧
            </el-button>
          </el-button-group>
        </div>
      </div>
      
      <!-- 操作按钮行 -->
      <div class="actions-row">
        <div class="left-actions">
          <el-button size="small" @click="handleScanRestore" :loading="isScanning">
            <el-icon><FolderOpened /></el-icon> 扫描恢复
          </el-button>
          <el-button size="small" @click="handleBatchScrape" :loading="isBatchScraping">
            <el-icon><Film /></el-icon> 批量刮削
          </el-button>
          <el-button size="small" @click="handleFixNfo" :loading="isFixingNfo">
            <el-icon><EditPen /></el-icon> 修复NFO
          </el-button>
          <el-button size="small" @click="confirmClearCompleted" :disabled="!completedDownloads?.length">
            <el-icon><Delete /></el-icon> 清除已完成
          </el-button>
          <el-button size="small" @click="confirmClearFailed" :disabled="!downloadStore.failedDownloads.length">
            <el-icon><Delete /></el-icon> 清除失败
          </el-button>
          <el-button
            size="small"
            :type="downloadStore.batchDeleteMode ? 'warning' : 'default'"
            @click="toggleBatchDeleteMode"
          >
            <el-icon><Delete /></el-icon>
            {{ downloadStore.batchDeleteMode ? '退出批量' : '批量删除' }}
          </el-button>
        </div>
        <div class="right-actions">
          <el-button-group>
            <el-button :disabled="!activeDownloads.length" @click="pauseAllDownloads" type="primary" size="small">
              <el-icon><VideoPause /></el-icon> 全部暂停
            </el-button>
            <el-button :disabled="!(downloadStore.pausedDownloads.length)" @click="resumeAllDownloads" type="success" size="small">
              <el-icon><VideoPlay /></el-icon> 全部继续
            </el-button>
          </el-button-group>
          <el-button size="small" @click="refreshDownloadList">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </div>

      <!-- 批量删除模式下的操作栏 -->
      <div v-if="downloadStore.batchDeleteMode" class="batch-action-bar">
        <div class="batch-info">
          <span class="batch-count">已选 {{ downloadStore.selectedDownloadsCount }} 项</span>
          <el-button text size="small" @click="selectAllInCurrentTab">全选当前列表</el-button>
          <el-button text size="small" @click="downloadStore.clearSelection()">取消选择</el-button>
        </div>
        <div class="batch-buttons">
          <el-button @click="toggleBatchDeleteMode">取消</el-button>
          <el-button
            type="danger"
            :disabled="!downloadStore.hasSelectedDownloads"
            @click="confirmBatchDelete"
          >
            <el-icon><Delete /></el-icon> 删除选中
          </el-button>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <div class="stats-container">
        <div class="download-stats">
          <div class="stat-card">
            <div class="stat-value">{{ activeDownloads?.length || 0 }}</div>
            <div class="stat-label">下载中</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ completedDownloads?.length || 0 }}</div>
            <div class="stat-label">已完成</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ downloadStore.failedDownloads.length || 0 }}</div>
            <div class="stat-label">已失败</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ allDownloads?.length || 0 }}</div>
            <div class="stat-label">总计</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ formatFileSize(totalDownloaded) }}</div>
            <div class="stat-label">已占用</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 列表视图 -->
    <div v-if="viewMode === 'list'" class="download-content">
      <el-tabs v-model="activeTab" class="download-tabs">
        <el-tab-pane label="全部下载" name="all">
          <download-list :filter="'all'" @play-video="handlePlayVideo" />
        </el-tab-pane>
        <el-tab-pane label="下载中" name="active">
          <download-list :filter="'active'" @play-video="handlePlayVideo" />
        </el-tab-pane>
        <el-tab-pane label="已完成" name="completed">
          <download-list :filter="'completed'" @play-video="handlePlayVideo" />
        </el-tab-pane>
        <el-tab-pane label="已失败" name="failed">
          <download-list :filter="'failed'" @play-video="handlePlayVideo" />
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 番剧分组视图 -->
    <div v-else class="group-content">
      <div v-if="isLoadingGroups" class="loading-placeholder">
        <el-skeleton :rows="3" animated />
      </div>
      <template v-else>
        <div v-if="filteredGroups.length === 0" class="empty-state">
          <el-empty description="暂无下载记录" />
        </div>
        <div v-else class="group-grid">
          <div 
            v-for="group in filteredGroups" 
            :key="group.series_name" 
            class="group-card"
            @click="openGroupDetail(group)"
          >
            <div class="group-cover">
              <img 
                v-if="group.cover_url" 
                :src="getCoverUrl(group.cover_url)" 
                :alt="group.series_name"
                referrerpolicy="no-referrer"
                loading="lazy"
                :class="{ 'blurred': shouldBlur && blurMode === 'blur' }"
              />
              <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
              <div v-else-if="shouldBlur && blurMode === 'hide'" class="hide-overlay">
                <el-icon :size="28"><Hide /></el-icon>
              </div>
              <div v-if="!group.cover_url" class="cover-placeholder">
                <el-icon :size="36"><VideoPlay /></el-icon>
              </div>
              <div class="group-badge">
                <span class="badge-count">{{ group.downloads.length }}</span>
                <span class="badge-label">集</span>
              </div>
            </div>
            <div class="group-info">
              <h3 class="group-title">{{ group.series_name }}</h3>
              <div class="group-meta">
                <span class="group-size">{{ formatFileSize(group.total_size) }}</span>
                <span v-if="group.downloading_count > 0" class="group-status downloading">
                  {{ group.downloading_count }} 下载中
                </span>
                <span v-else-if="group.failed_count > 0" class="group-status failed">
                  {{ group.failed_count }} 失败
                </span>
                <span v-else class="group-status completed">全部完成</span>
              </div>
              <el-progress 
                :percentage="Math.round(group.completed_count / group.downloads.length * 100)"
                :stroke-width="3"
                :show-text="false"
                :color="group.downloading_count > 0 ? '#409EFF' : group.failed_count > 0 ? '#F56C6C' : '#67C23A'"
              />
              <div class="group-actions" v-if="group.completed_count > 0">
                <el-button size="small" text type="primary" @click.stop="handleScrapeSeries(group.series_name)">
                  <el-icon><Film /></el-icon> 刮削
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <!-- 番剧详情弹窗 -->
    <el-dialog
      v-model="groupDetailVisible"
      :title="currentGroup?.series_name || '番剧详情'"
      width="80%"
      destroy-on-close
      top="5vh"
    >
      <div v-if="currentGroup" class="group-detail">
        <div class="detail-stats">
          <el-tag type="success">{{ currentGroup.completed_count }} 已完成</el-tag>
          <el-tag v-if="currentGroup.downloading_count > 0" type="primary">{{ currentGroup.downloading_count }} 下载中</el-tag>
          <el-tag v-if="currentGroup.failed_count > 0" type="danger">{{ currentGroup.failed_count }} 失败</el-tag>
          <el-tag type="info">共 {{ formatFileSize(currentGroup.total_size) }}</el-tag>
        </div>
        <div class="detail-episodes">
          <div v-for="dl in currentGroup.downloads" :key="dl.video_id" class="episode-item" @click="handleEpisodeClick(dl)">
            <div class="episode-cover">
              <img 
                v-if="dl.cover_url" 
                :src="getCoverUrl(dl.cover_url)" 
                referrerpolicy="no-referrer"
                loading="lazy"
              />
              <div v-else class="cover-placeholder small">
                <el-icon><VideoPlay /></el-icon>
              </div>
            </div>
            <div class="episode-info">
              <span class="episode-title">{{ extractFilename(dl.filename) || dl.title }}</span>
              <span class="episode-size">{{ formatFileSize(dl.total_size) }}</span>
            </div>
            <el-tag :type="getStatusType(dl.status)" size="small">{{ getStatusText(dl.status) }}</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 视频播放器弹窗 -->
    <el-dialog
      v-model="videoPlayerVisible"
      :title="currentVideo.title || '离线播放'"
      width="80%"
      destroy-on-close
      top="5vh"
      class="video-dialog"
      :before-close="closeVideoPlayer"
    >
      <div class="video-player-wrapper">
        <VideoPlayer
          v-if="videoPlayerVisible"
          :streamUrls="[{ url: currentVideo.url, quality: '原始质量' }]"
          :coverUrl="currentVideo.cover_url"
          :title="currentVideo.title"
          :autoPlay="true"
          :showDebugInfo="false"
        />
      </div>
    </el-dialog>

    <!-- 批量删除确认对话框 -->
    <el-dialog
      v-model="batchDeleteDialogVisible"
      title="批量删除确认"
      width="420px"
      :width="isMobile ? '90%' : '420px'"
    >
      <div class="batch-delete-dialog-content">
        <p class="dialog-text">
          即将删除选中的 <strong>{{ downloadStore.selectedDownloadsCount }}</strong> 条下载记录
        </p>
        <div class="dialog-option">
          <el-checkbox v-model="batchDeleteDeleteFiles">
            同时删除源文件
          </el-checkbox>
          <p class="option-hint">
            勾选后将删除：视频文件、刮削生成的 NFO 元数据文件、封面和缩略图等图片文件；<br/>
            不勾选则仅删除下载记录，保留所有文件。
          </p>
        </div>
      </div>
      <template #footer>
        <el-button @click="batchDeleteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          :loading="false"
          @click="executeBatchDelete"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useDownloadStore } from '../stores/download';
import { storeToRefs } from 'pinia';
import DownloadList from '../components/DownloadList.vue';
import VideoPlayer from '../components/VideoPlayer.vue';
import { VideoPause, VideoPlay, Delete, Refresh, List, Grid, FolderOpened, Hide, Film, EditPen } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { DownloadApi } from '../api/download';
import { ScrapeApi } from '../api/scrape';
import { useContentSettings } from '../composables/useContentSettings';

const downloadStore = useDownloadStore();
const { 
  activeDownloads, 
  completedDownloads,
  allDownloads,
  totalDownloaded,
} = storeToRefs(downloadStore);

const { shouldBlur, mode: blurMode } = useContentSettings();

// 视图状态
const viewMode = ref<'list' | 'group'>('list');
const activeTab = ref('all');
const searchQuery = ref('');
const isMobile = ref(window.innerWidth <= 480);

// 窗口大小变化处理
const handleResize = () => {
  isMobile.value = window.innerWidth <= 480;
};

// 分组视图状态
const groups = ref<any[]>([]);
const isLoadingGroups = ref(false);
const groupDetailVisible = ref(false);
const currentGroup = ref<any>(null);

// 视频播放状态
const videoPlayerVisible = ref(false);
const currentVideo = ref<{ video_id: string; url: string; title: string; cover_url: string }>({
  video_id: '', url: '', title: '', cover_url: ''
});

// 扫描状态
const isScanning = ref(false);

// 刮削状态
const isBatchScraping = ref(false);
const isFixingNfo = ref(false);

// 搜索过滤
let searchTimer: ReturnType<typeof setTimeout> | null = null;
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    downloadStore.initializeDownloads();
  }, 300);
};

// 加载番剧分组
const loadGroups = async () => {
  isLoadingGroups.value = true;
  try {
    groups.value = await DownloadApi.getDownloadGroups();
  } finally {
    isLoadingGroups.value = false;
  }
};

// 过滤分组（按搜索关键词）
const filteredGroups = computed(() => {
  if (!searchQuery.value) return groups.value;
  const q = searchQuery.value.toLowerCase();
  return groups.value.filter(g => g.series_name.toLowerCase().includes(q));
});

// 打开番剧详情
const openGroupDetail = (group: any) => {
  currentGroup.value = group;
  groupDetailVisible.value = true;
};

// 获取封面URL
const getCoverUrl = (coverUrl: string) => {
  if (!coverUrl) return '';
  if (coverUrl.startsWith('/api/')) {
    const token = localStorage.getItem('token');
    return `${coverUrl}${coverUrl.includes('?') ? '&' : '?'}token=${token}`;
  }
  return coverUrl;
};

// 从文件名提取标题
const extractFilename = (filename: string): string => {
  if (!filename) return '';
  const name = filename.split('/').pop() || filename;
  const match = name.match(/^[^_]+_(.+)\.mp4$/);
  return match ? match[1] : name.replace('.mp4', '');
};

// 格式化文件大小
const formatFileSize = (bytes: number | undefined): string => {
  if (bytes === undefined || isNaN(bytes)) return '0 B';
  return DownloadApi.formatFileSize(bytes);
};

// 获取状态标签类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success';
    case 'error': case 'cancelled': return 'danger';
    case 'downloading': case 'paused': case 'pending': return 'primary';
    default: return 'info';
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '准备中', downloading: '下载中', paused: '已暂停',
    completed: '已完成', cancelled: '已取消', error: '失败'
  };
  return map[status] || status;
};

// 点击集数
const handleEpisodeClick = (dl: any) => {
  if (dl.status === 'completed') {
    currentVideo.value = {
      video_id: dl.video_id,
      url: DownloadApi.getVideoFileUrl(dl.video_id),
      title: extractFilename(dl.filename) || dl.title,
      cover_url: dl.cover_url
    };
    videoPlayerVisible.value = true;
  } else {
    // 跳转到视频详情页
    window.open(`/video/${dl.video_id}`, '_blank');
  }
};

// 批量刮削
const handleBatchScrape = async () => {
  try {
    await ElMessageBox.confirm(
      '将对所有已下载的番剧目录生成NFO元数据文件（tvshow.nfo/movie.nfo）和封面图片，便于绿联NAS影视中心识别。是否继续？',
      '批量刮削',
      { confirmButtonText: '开始刮削', cancelButtonText: '取消', type: 'info' }
    );
  } catch { return; }

  isBatchScraping.value = true;
  try {
    const results = await ScrapeApi.batchScrape([], 'tv_show');
    const successCount = results.filter(r => r.is_success).length;
    const failCount = results.filter(r => !r.is_success).length;
    if (successCount > 0) {
      ElMessage.success(`刮削完成: ${successCount} 个成功${failCount > 0 ? `, ${failCount} 个失败` : ''}`);
    } else if (results.length === 0) {
      ElMessage.info('未发现可刮削的番剧目录');
    } else {
      ElMessage.error('刮削全部失败');
    }
  } catch (e) {
    ElMessage.error('批量刮削失败');
  } finally {
    isBatchScraping.value = false;
  }
};

// 修复NFO空标签
const handleFixNfo = async () => {
  try {
    await ElMessageBox.confirm(
      '将扫描所有 NFO 文件，移除空日期标签（如 <year/>、<premiered/>），修复绿联影视中心显示 1970 年的问题。',
      '修复 NFO 日期标签',
      { confirmButtonText: '开始修复', cancelButtonText: '取消', type: 'info' }
    );
  } catch {
    return;
  }

  isFixingNfo.value = true;
  try {
    const result = await ScrapeApi.fixNfoEmptyTags();
    if (result.fixed > 0) {
      ElMessage.success(`修复完成: 扫描 ${result.total} 个 NFO，修复 ${result.fixed} 个文件`);
    } else {
      ElMessage.success(`扫描 ${result.total} 个 NFO，无需修复`);
    }
  } catch (e) {
    ElMessage.error('修复 NFO 失败');
  } finally {
    isFixingNfo.value = false;
  }
};

// 单个番剧刮削
const handleScrapeSeries = async (seriesName: string) => {
  try {
    const result = await ScrapeApi.scrapeSeries({
      series_name: seriesName,
      scrape_mode: 'tv_show',
      is_rename_file: true,
      is_reorganize_directory: true
    });
    if (result.is_success) {
      ElMessage.success(`刮削完成: ${seriesName}`);
    } else {
      ElMessage.error(`刮削失败: ${result.error_message || '未知错误'}`);
    }
  } catch (e) {
    ElMessage.error('刮削失败');
  }
};

// 扫描恢复
const handleScanRestore = async () => {
  try {
    await ElMessageBox.confirm(
      '将扫描下载目录，自动恢复文件存在但记录丢失的下载项，并清理文件已不存在的无效记录。是否继续？',
      '扫描恢复',
      { confirmButtonText: '开始扫描', cancelButtonText: '取消', type: 'info' }
    );
  } catch { return; }

  isScanning.value = true;
  try {
    const result = await DownloadApi.scanAndRestore();
    const messages = [];
    if (result.total_restored > 0) {
      messages.push(`恢复 ${result.total_restored} 条记录`);
    }
    if (result.total_removed > 0) {
      messages.push(`清理 ${result.total_removed} 条无效记录`);
    }
    if (messages.length > 0) {
      ElMessage.success(messages.join('，'));
      await downloadStore.initializeDownloads();
      if (viewMode.value === 'group') await loadGroups();
    } else {
      ElMessage.info('未发现需要恢复或清理的记录');
    }
  } catch (e) {
    ElMessage.error('扫描恢复失败');
  } finally {
    isScanning.value = false;
  }
};

// 清除已完成
const confirmClearCompleted = async () => {
  try {
    await ElMessageBox.confirm('确定清除所有已完成的下载记录吗？文件不会被删除。', '清除已完成', 
      { confirmButtonText: '清除', cancelButtonText: '取消', type: 'warning' });
    const result = await DownloadApi.clearCompleted();
    if (result.status === 'success') {
      ElMessage.success(result.message);
      await downloadStore.initializeDownloads();
      if (viewMode.value === 'group') await loadGroups();
    }
  } catch {}
};

// 清除失败
const confirmClearFailed = async () => {
  try {
    await ElMessageBox.confirm('确定清除所有失败的下载记录吗？', '清除失败',
      { confirmButtonText: '清除', cancelButtonText: '取消', type: 'warning' });
    const result = await DownloadApi.clearFailed();
    if (result.status === 'success') {
      ElMessage.success(result.message);
      await downloadStore.initializeDownloads();
      if (viewMode.value === 'group') await loadGroups();
    }
  } catch {}
};

// 切换批量删除模式
const toggleBatchDeleteMode = () => {
  downloadStore.toggleBatchDeleteMode();
  if (downloadStore.batchDeleteMode) {
    ElMessage.info('已进入批量删除模式，点击下载项进行选择');
  }
};

// 全选当前标签下的所有下载项
const selectAllInCurrentTab = () => {
  let itemsToSelect: any[] = [];
  switch (activeTab.value) {
    case 'active':
      itemsToSelect = downloadStore.activeDownloads;
      break;
    case 'completed':
      itemsToSelect = downloadStore.completedDownloads;
      break;
    case 'failed':
      itemsToSelect = downloadStore.failedDownloads;
      break;
    default:
      itemsToSelect = downloadStore.allDownloads;
  }
  downloadStore.selectAll(itemsToSelect);
};

// 确认批量删除（打开对话框询问是否删除源文件）
const batchDeleteDialogVisible = ref(false);
const batchDeleteDeleteFiles = ref(true);

const confirmBatchDelete = () => {
  if (!downloadStore.hasSelectedDownloads) {
    ElMessage.warning('请先选择要删除的下载项');
    return;
  }
  // 重置默认值：默认删除源文件
  batchDeleteDeleteFiles.value = true;
  batchDeleteDialogVisible.value = true;
};

// 执行批量删除
const executeBatchDelete = async () => {
  const deleteFiles = batchDeleteDeleteFiles.value;
  batchDeleteDialogVisible.value = false;

  const result = await downloadStore.deleteSelected(deleteFiles);
  if (result) {
    await downloadStore.initializeDownloads();
    if (viewMode.value === 'group') await loadGroups();
  }
};

// 全部暂停
const pauseAllDownloads = async () => {
  await downloadStore.pauseAllDownloads();
  ElMessage.success('已暂停所有下载');
};

// 全部继续
const resumeAllDownloads = async () => {
  await downloadStore.resumeAllDownloads();
  ElMessage.success('已恢复所有下载');
};

// 刷新列表
const refreshDownloadList = async () => {
  await downloadStore.initializeDownloads();
  if (viewMode.value === 'group') await loadGroups();
};

// 播放视频
const handlePlayVideo = (videoInfo: any) => {
  currentVideo.value = videoInfo;
  videoPlayerVisible.value = true;
};

// 关闭播放器
const closeVideoPlayer = () => {
  videoPlayerVisible.value = false;
  setTimeout(() => {
    currentVideo.value = { video_id: '', url: '', title: '', cover_url: '' };
  }, 200);
};

// 初始化
onMounted(async () => {
  await downloadStore.initializeDownloads();
  downloadStore.startPolling();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  downloadStore.stopPolling();
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.downloads-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
  overflow-x: hidden;
}

.downloads-header {
  margin-bottom: 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.header-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-input {
  width: 200px;
}

.view-toggle {
  flex-shrink: 0;
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.left-actions, .right-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.stats-container {
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.download-stats {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.stat-card {
  background-color: var(--bg-color);
  border-radius: 6px;
  padding: 10px 15px;
  flex: 1;
  min-width: 80px;
  text-align: center;
  box-shadow: var(--card-shadow);
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary-color);
  margin-top: 5px;
}

.download-content {
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  padding: 15px;
}

/* 番剧分组视图 */
.group-content {
  min-height: 200px;
}

.loading-placeholder {
  padding: 40px;
}

.empty-state {
  padding: 60px 0;
}

.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.group-card {
  background-color: var(--bg-secondary-color);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--card-shadow);
}

.group-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.group-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  overflow: hidden;
  background-color: var(--bg-color);
}

.group-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.group-card:hover .group-cover img {
  transform: scale(1.05);
}

.group-cover img.blurred {
  filter: blur(15px) brightness(0.8);
  transform: scale(1.1);
}

.group-cover .blur-overlay,
.group-cover .hide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
}

.group-cover .hide-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary-color), var(--bg-color));
  color: var(--text-secondary-color);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary-color), var(--bg-color));
  color: var(--text-secondary-color);
}

.cover-placeholder.small {
  width: 56px;
  height: 32px;
  border-radius: 4px;
  flex-shrink: 0;
}

.cover-placeholder.small .el-icon {
  font-size: 18px;
}

.group-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  border-radius: 12px;
  padding: 3px 8px;
  display: flex;
  align-items: baseline;
  gap: 2px;
  z-index: 3;
}

.badge-count {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.badge-label {
  color: rgba(255,255,255,0.7);
  font-size: 11px;
}

.group-info {
  padding: 12px;
}

.group-title {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
}

.group-size {
  color: var(--text-secondary-color);
}

.group-status {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
}

.group-status.completed {
  color: #67C23A;
  background: rgba(103, 194, 58, 0.1);
}

.group-status.downloading {
  color: #409EFF;
  background: rgba(64, 158, 255, 0.1);
}

.group-status.failed {
  color: #F56C6C;
  background: rgba(245, 108, 108, 0.1);
}

/* 番剧详情弹窗 */
.detail-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.detail-episodes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 60vh;
  overflow-y: auto;
}

.episode-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background-color: var(--bg-secondary-color);
  cursor: pointer;
  transition: all 0.2s;
}

.episode-item:hover {
  background-color: var(--hover-bg-color);
}

.episode-cover {
  width: 56px;
  height: 32px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
  background-color: var(--bg-color);
}

.episode-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.episode-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.episode-title {
  font-size: 14px;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.episode-size {
  font-size: 12px;
  color: var(--text-secondary-color);
}

.video-player-wrapper {
  width: 100%;
  aspect-ratio: 16 / 9;
}

.video-dialog :deep(.el-dialog__body) {
  padding: 10px;
}

/* 批量删除操作栏 */
.batch-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 15px;
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.12), rgba(230, 162, 60, 0.12));
  border: 1px solid rgba(245, 108, 108, 0.3);
  border-radius: 10px;
  flex-wrap: wrap;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--danger-color, #F56C6C);
}

.batch-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 批量删除对话框 */
.batch-delete-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-text {
  margin: 0;
  font-size: 15px;
  color: var(--text-color);
  line-height: 1.6;
}

.dialog-text strong {
  color: var(--danger-color, #F56C6C);
  font-size: 18px;
  margin: 0 4px;
}

.dialog-option {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
}

.option-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary-color);
  line-height: 1.5;
}

/* PC端大气布局 */
@media (min-width: 769px) {
  .downloads-page {
    padding: 32px 28px;
  }

  .page-title {
    font-size: 28px;
  }

  .downloads-header {
    margin-bottom: 24px;
  }

  .search-input {
    width: 280px;
  }

  .stats-container {
    padding: 20px 24px;
    margin-bottom: 24px;
    border-radius: 12px;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 14px;
  }

  .group-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
  }

  .group-info {
    padding: 14px 16px;
  }

  .group-title {
    font-size: 15px;
  }

  .group-meta {
    font-size: 13px;
  }

  .download-content {
    padding: 20px 24px;
    border-radius: 12px;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .downloads-page { padding: 10px; }
  .header-top { flex-direction: column; align-items: stretch; }
  .header-toolbar { justify-content: space-between; }
  .search-input { flex: 1; }
  .actions-row { flex-direction: column; }
  .left-actions {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }
  .right-actions {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
  }
  .download-stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  .stat-card { min-width: 0; flex: none; }
  .group-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  /* 批量操作栏手机端垂直布局 */
  .batch-action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    padding: 10px;
  }
  .batch-info {
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
  }
  .batch-buttons {
    width: 100%;
  }
  .batch-buttons .el-button {
    flex: 1;
  }
}

@media (max-width: 480px) {
  .downloads-page { padding: 5px; }
  .page-title { font-size: 20px; }
  .search-input { width: 100%; }
  .header-toolbar { flex-wrap: wrap; }
  .download-stats { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .stat-card { padding: 8px; }
  .stat-value { font-size: 16px; }
  .stat-label { font-size: 12px; }
  /* 手机端每行2个按钮，5个按钮=3行（2+2+1） */
  .left-actions { grid-template-columns: repeat(2, 1fr); gap: 5px; }
  .right-actions { grid-template-columns: repeat(2, 1fr); gap: 5px; }
  .group-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .group-title { font-size: 13px; }
}
</style>
