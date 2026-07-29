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
          <el-button size="small" @click="handleScanRestore" :loading="isScanning" :disabled="isLoadingGroups">
            <el-icon><FolderOpened /></el-icon> 扫描恢复
          </el-button>
          <el-button size="small" @click="handleBatchScrape" :loading="isBatchScraping" :disabled="isLoadingGroups">
            <el-icon><Film /></el-icon> 批量刮削
          </el-button>
          <el-button size="small" @click="handleFixNfo" :loading="isFixingNfo" :disabled="isLoadingGroups">
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
            :disabled="isLoadingGroups"
          >
            <el-icon><Delete /></el-icon>
            {{ downloadStore.batchDeleteMode ? '退出批量' : '批量删除' }}
          </el-button>
          <el-button
            size="small"
            type="warning"
            @click="openMergeSeriesDialog"
            :disabled="isLoadingGroups"
          >
            <el-icon><Connection /></el-icon> 合并系列
          </el-button>
        </div>
        <div class="right-actions">
          <span class="page-size-label">每页</span>
          <el-select v-model="pageSize" size="small" style="width: 70px;">
            <el-option v-for="s in pageSizeOptions" :key="s" :label="s" :value="s" />
          </el-select>
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
          <!-- 合集分组列表 -->
          <div v-if="isLoadingGroups" class="loading-placeholder">
            <el-skeleton :rows="5" animated />
          </div>
          <template v-else>
            <div v-if="listAllTotal === 0" class="empty-state">
              <el-empty description="暂无下载记录" />
            </div>
            <div v-else class="collapsible-group-list">
              <!-- 合集分组 -->
              <div v-for="item in listAllPaginatedItems" :key="item.type === 'group' ? item.data.series_name : '__ungrouped__'" class="collapsible-group">
                <template v-if="item.type === 'group'">
                <div class="group-row" @click="toggleGroupExpand(item.data.series_name)">
                  <div class="group-row-cover">
                    <img v-if="item.data.cover_url" :src="getCoverUrl(item.data.cover_url)" :alt="item.data.series_name" referrerpolicy="no-referrer" loading="lazy" :class="{ 'blurred': shouldBlur && blurMode === 'blur' }" />
                    <div v-if="shouldBlur && blurMode === 'blur'" class="blur-overlay"></div>
                    <div v-else-if="shouldBlur && blurMode === 'hide'" class="hide-overlay"><el-icon :size="18"><Hide /></el-icon></div>
                    <div v-if="!item.data.cover_url" class="cover-placeholder small"><el-icon :size="18"><VideoPlay /></el-icon></div>
                  </div>
                  <el-icon class="expand-icon" :class="{ 'is-expanded': expandedGroups.has(item.data.series_name) }"><ArrowRight /></el-icon>
                  <div class="group-row-info">
                    <h3 class="group-row-title">{{ item.data.series_name }}</h3>
                    <div class="group-row-meta">
                      <span>{{ item.data.downloads.length }}集</span>
                      <span>·</span>
                      <span>{{ formatFileSize(item.data.total_size) }}</span>
                      <span v-if="item.data.downloading_count > 0" class="group-status downloading">{{ item.data.downloading_count }} 下载中</span>
                      <span v-else-if="item.data.failed_count > 0" class="group-status failed">{{ item.data.failed_count }} 失败</span>
                      <span v-else class="group-status completed">全部完成</span>
                    </div>
                  </div>
                  <div class="group-row-actions">
                    <el-button v-if="item.data.completed_count > 0" size="small" text type="primary" @click.stop="handleScrapeSeries(item.data.series_name)" :loading="isScrapingSingle && scrapingSeriesName === item.data.series_name">
                      <el-icon><Film /></el-icon> 重新刮削
                    </el-button>
                  </div>
                </div>
                <!-- 展开的集列表 -->
                <div v-if="expandedGroups.has(item.data.series_name)" class="group-episodes">
                  <div v-for="dl in filterDownloadsByTab(item.data.downloads)" :key="dl.video_id" class="episode-row" @click="handleEpisodeClick(dl)">
                    <div class="episode-row-cover">
                      <img v-if="dl.cover_url" :src="getCoverUrl(dl.cover_url)" referrerpolicy="no-referrer" loading="lazy" />
                      <div v-else class="cover-placeholder small"><el-icon :size="14"><VideoPlay /></el-icon></div>
                    </div>
                    <div class="episode-row-info">
                      <span class="episode-row-title">{{ extractFilename(dl.filename) || dl.title }}</span>
                      <span class="episode-row-size">{{ formatFileSize(dl.total_size) }}</span>
                    </div>
                    <div class="episode-row-actions">
                      <el-tag :type="getStatusType(dl.status)" size="small">{{ getStatusText(dl.status) }}</el-tag>
                      <el-button v-if="dl.status === 'completed'" size="small" text type="primary" @click.stop="handleSetPoster(item.data.series_name, dl.video_id)" :loading="isSettingPoster === dl.video_id">
                        <el-icon><Picture /></el-icon> 设为合集海报
                      </el-button>
                    </div>
                  </div>
                </div>
                </template>
                <!-- 未分组 -->
                <template v-else>
                <div class="group-row" @click="toggleGroupExpand('__ungrouped__')">
                  <el-icon class="expand-icon" :class="{ 'is-expanded': expandedGroups.has('__ungrouped__') }"><ArrowRight /></el-icon>
                  <div class="group-row-info">
                    <h3 class="group-row-title ungrouped-title">未分组</h3>
                    <div class="group-row-meta">
                      <span>{{ ungroupedDownloadsFiltered.length }}个视频</span>
                    </div>
                  </div>
                </div>
                <div v-if="expandedGroups.has('__ungrouped__')" class="group-episodes">
                  <div v-for="dl in ungroupedDownloadsFiltered" :key="dl.video_id" class="episode-row" @click="handleEpisodeClick(dl)">
                    <div class="episode-row-cover">
                      <img v-if="dl.cover_url" :src="getCoverUrl(dl.cover_url)" referrerpolicy="no-referrer" loading="lazy" />
                      <div v-else class="cover-placeholder small"><el-icon :size="14"><VideoPlay /></el-icon></div>
                    </div>
                    <div class="episode-row-info">
                      <span class="episode-row-title">{{ extractFilename(dl.filename) || dl.title }}</span>
                      <span class="episode-row-size">{{ formatFileSize(dl.total_size) }}</span>
                    </div>
                    <div class="episode-row-actions">
                      <el-tag :type="getStatusType(dl.status)" size="small">{{ getStatusText(dl.status) }}</el-tag>
                    </div>
                  </div>
                </div>
                </template>
              </div>
              <!-- 分页 -->
              <div class="pagination-container" v-if="listAllTotal > pageSize">
                <el-pagination
                  v-model:current-page="listAllCurrentPage"
                  :page-size="pageSize"
                  :total="listAllTotal"
                  layout="prev, pager, next"
                  small
                  background
                />
              </div>
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="下载中" name="active">
          <download-list :filter="'active'" :page-size="pageSize" @play-video="handlePlayVideo" />
        </el-tab-pane>
        <el-tab-pane label="已完成" name="completed">
          <download-list :filter="'completed'" :page-size="pageSize" @play-video="handlePlayVideo" />
        </el-tab-pane>
        <el-tab-pane label="已失败" name="failed">
          <download-list :filter="'failed'" :page-size="pageSize" @play-video="handlePlayVideo" />
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 番剧分组视图 -->
    <div v-else class="group-content">
      <div v-if="isLoadingGroups" class="loading-placeholder">
        <div class="skeleton-group-grid">
          <div class="skeleton-group-card skeleton-shimmer" v-for="i in 6" :key="'skg-'+i">
            <div class="skeleton-group-cover"></div>
            <div class="skeleton-group-info">
              <div class="skeleton-line skeleton-shimmer" style="width: 70%; height: 16px;"></div>
              <div class="skeleton-line skeleton-shimmer" style="width: 40%; height: 12px; margin-top: 6px;"></div>
            </div>
          </div>
        </div>
      </div>
      <template v-else>
        <div v-if="filteredGroups.length === 0" class="empty-state">
          <el-empty description="暂无下载记录" />
        </div>
        <template v-else>
        <div class="group-grid">
          <div
            v-for="group in groupPaginatedItems"
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
                  <el-icon><Film /></el-icon> 重新刮削
                </el-button>
              </div>
            </div>
          </div>
        </div>
        <div class="pagination-container" v-if="groupTotal > pageSize">
          <el-pagination
            v-model:current-page="groupCurrentPage"
            :page-size="pageSize"
            :total="groupTotal"
            layout="prev, pager, next"
            small
            background
          />
        </div>
        </template>
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
          <el-button size="small" type="primary" @click="handleScrapeSeries(currentGroup.series_name)" :loading="isScrapingSingle">
            <el-icon><Film /></el-icon> 重新刮削
          </el-button>
        </div>
        <div class="detail-episodes">
          <div v-for="dl in detailPaginatedDownloads" :key="dl.video_id" class="episode-item" @click="handleEpisodeClick(dl)">
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
            <div class="episode-actions">
              <el-tag :type="getStatusType(dl.status)" size="small">{{ getStatusText(dl.status) }}</el-tag>
              <el-button v-if="dl.status === 'completed'" size="small" text type="primary" @click.stop="handleSetPoster(currentGroup.series_name, dl.video_id)" :loading="isSettingPoster === dl.video_id">
                <el-icon><Picture /></el-icon> 设为合集海报
              </el-button>
            </div>
          </div>
        </div>
        <div class="pagination-container" v-if="detailTotal > pageSize">
          <el-pagination
            v-model:current-page="detailCurrentPage"
            :page-size="pageSize"
            :total="detailTotal"
            layout="prev, pager, next"
            small
            background
          />
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

    <!-- 合并系列对话框 -->
    <el-dialog
      v-model="mergeSeriesDialogVisible"
      title="合并系列"
      width="80%"
      :width="isMobile ? '95%' : '80%'"
      class="merge-series-dialog"
    >
      <div class="merge-series-content">
        <div class="merge-series-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>选择两个或更多已下载的番剧，合并到同一个系列中</span>
        </div>

        <div class="merge-series-name-row">
          <span class="merge-label">系列名称：</span>
          <el-input v-model="mergeSeriesNameInput" placeholder="输入系列名称" style="flex: 1;" />
        </div>

        <div class="merge-series-select">
          <h4 class="merge-select-title">选择番剧</h4>
          <el-table
            ref="mergeSelectTableRef"
            :data="completedDownloadsList"
            border
            stripe
            size="default"
            @selection-change="handleMergeSelectionChange"
            class="merge-select-table"
          >
            <el-table-column type="selection" width="50" align="center" />
            <el-table-column label="番剧名称" min-width="200">
              <template #default="{ row }">
                <span>{{ extractFilename(row.filename) || row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="系列" width="150">
              <template #default="{ row }">
                <span>{{ row.series_name || '未分组' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="100" align="center">
              <template #default="{ row }">
                <span>{{ formatFileSize(row.total_size) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="merge-series-plan" v-if="mergeSelectedDownloads.length > 0">
          <h4 class="merge-select-title">季号分配</h4>
          <el-table :data="mergeSelectedDownloads" border size="default" class="merge-plan-table">
            <el-table-column label="番剧名称" min-width="200">
              <template #default="{ row }">
                <span>{{ extractFilename(row.filename) || row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="季号" width="120" align="center">
              <template #default="{ $index }">
                <el-input-number
                  v-model="mergeSeasonNumbers[$index]"
                  :min="1"
                  :max="99"
                  size="small"
                  controls-position="right"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="mergeSeriesDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="isMergingSeries"
            :disabled="mergeSelectedDownloads.length < 2 || !mergeSeriesNameInput.trim()"
            @click="executeMergeSeries"
          >
            确认合并 ({{ mergeSelectedDownloads.length }})
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量刮削进度对话框（v3.3.9 新增） -->
    <el-dialog
      v-model="batchScrapeProgress.visible"
      title="批量刮削进度"
      width="600px"
      :width="isMobile ? '95%' : '600px'"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="batch-progress-content">
        <div class="progress-summary">
          <el-progress
            :percentage="batchScrapeProgress.percentage"
            :status="batchScrapeProgress.status"
            :stroke-width="10"
          />
          <div class="progress-text">
            {{ batchScrapeProgress.completed }} / {{ batchScrapeProgress.total }}
            <span v-if="batchScrapeProgress.successCount > 0" class="progress-success">
              成功 {{ batchScrapeProgress.successCount }}
            </span>
            <span v-if="batchScrapeProgress.failCount > 0" class="progress-fail">
              失败 {{ batchScrapeProgress.failCount }}
            </span>
          </div>
        </div>
        <div class="progress-current" v-if="batchScrapeProgress.currentSeries">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在处理: {{ batchScrapeProgress.currentSeries }}</span>
        </div>
        <div class="progress-list" v-if="batchScrapeProgress.results.length > 0">
          <div class="progress-list-header">处理结果</div>
          <div class="progress-list-body">
            <div
              v-for="(item, idx) in batchScrapeProgress.results"
              :key="idx"
              class="progress-list-item"
              :class="{ 'is-success': item.is_success, 'is-fail': !item.is_success }"
            >
              <el-icon v-if="item.is_success"><CircleCheck /></el-icon>
              <el-icon v-else><CircleClose /></el-icon>
              <span class="item-name">{{ item.series_name }}</span>
              <span v-if="!item.is_success" class="item-error">{{ item.error_message }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button
          v-if="!batchScrapeProgress.running"
          type="primary"
          @click="closeBatchScrapeProgress"
        >
          关闭
        </el-button>
        <el-button v-else disabled :loading="true">处理中...</el-button>
      </template>
    </el-dialog>

    <!-- 修复 NFO 进度对话框（v3.3.9 新增） -->
    <el-dialog
      v-model="fixNfoProgress.visible"
      title="修复 NFO 进度"
      width="500px"
      :width="isMobile ? '95%' : '500px'"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="batch-progress-content">
        <div class="progress-summary">
          <el-progress
            :percentage="100"
            :status="fixNfoProgress.status"
            :stroke-width="10"
          />
        </div>
        <div class="progress-text" v-if="fixNfoProgress.running">
          正在扫描 NFO 文件...
        </div>
        <div v-else class="fix-nfo-result">
          <div class="result-row">
            <span class="result-label">扫描文件总数</span>
            <span class="result-value">{{ fixNfoProgress.total }}</span>
          </div>
          <div class="result-row">
            <span class="result-label">修复文件数量</span>
            <span class="result-value" :class="{ 'has-fixed': fixNfoProgress.fixed > 0 }">
              {{ fixNfoProgress.fixed }}
            </span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button
          v-if="!fixNfoProgress.running"
          type="primary"
          @click="closeFixNfoProgress"
        >
          关闭
        </el-button>
        <el-button v-else disabled :loading="true">处理中...</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useDownloadStore } from '../stores/download';
import { storeToRefs } from 'pinia';
import DownloadList from '../components/DownloadList.vue';
import VideoPlayer from '../components/VideoPlayer.vue';
import { VideoPause, VideoPlay, Delete, Refresh, List, Grid, FolderOpened, Hide, Film, EditPen, Connection, InfoFilled, Loading, CircleCheck, CircleClose, Picture, ArrowRight } from '@element-plus/icons-vue';
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
// 视图切换时加载分组数据
const viewMode = ref<'list' | 'group'>('list');
const activeTab = ref('all');
const searchQuery = ref('');
const isMobile = ref(window.innerWidth <= 480);

// 分页状态
const pageSize = ref(5);
const pageSizeOptions = [5, 10, 20, 50];
const listAllCurrentPage = ref(1);    // 列表视图-全部tab
const groupCurrentPage = ref(1);      // 番剧视图
const detailCurrentPage = ref(1);     // 番剧详情弹窗

// 窗口大小变化处理
const handleResize = () => {
  isMobile.value = window.innerWidth <= 480;
};

// 分组视图状态
const groups = ref<any[]>([]);
const isLoadingGroups = ref(false);
const groupDetailVisible = ref(false);
const currentGroup = ref<any>(null);

// v3.5.2: 列表视图可折叠合集
const expandedGroups = ref<Set<string>>(new Set());
const isScrapingSingle = ref(false);
const scrapingSeriesName = ref('');
const isSettingPoster = ref<string | null>(null);

// 未分组下载项（series_name 为空的）
const ungroupedDownloads = computed(() => {
  const allGroupedVideoIds = new Set<string>();
  for (const group of groups.value) {
    for (const dl of group.downloads) {
      allGroupedVideoIds.add(dl.video_id);
    }
  }
  return (downloadStore.allDownloads || []).filter(dl => !allGroupedVideoIds.has(dl.video_id));
});

const ungroupedDownloadsFiltered = computed(() => {
  return filterDownloadsByTab(ungroupedDownloads.value);
});

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

// v3.3.9: 批量刮削进度状态
interface BatchScrapeProgress {
  visible: boolean;
  running: boolean;
  total: number;
  completed: number;
  successCount: number;
  failCount: number;
  currentSeries: string;
  results: Array<{ series_name: string; is_success: boolean; error_message?: string }>;
  percentage: number;
  status: '' | 'success' | 'exception' | 'warning';
}

const batchScrapeProgress = ref<BatchScrapeProgress>({
  visible: false,
  running: false,
  total: 0,
  completed: 0,
  successCount: 0,
  failCount: 0,
  currentSeries: '',
  results: [],
  percentage: 0,
  status: ''
});

const closeBatchScrapeProgress = () => {
  batchScrapeProgress.value.visible = false;
};

// v3.3.9: 修复 NFO 进度状态
interface FixNfoProgress {
  visible: boolean;
  running: boolean;
  total: number;
  fixed: number;
  status: '' | 'success' | 'exception' | 'warning';
}

const fixNfoProgress = ref<FixNfoProgress>({
  visible: false,
  running: false,
  total: 0,
  fixed: 0,
  status: ''
});

const closeFixNfoProgress = () => {
  fixNfoProgress.value.visible = false;
};

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

// 列表视图-全部tab：合并合集+未分组为统一列表用于分页
const listAllItems = computed(() => {
  const items: Array<{ type: 'group' | 'ungrouped'; data: any }> = [];
  for (const group of filteredGroups.value) {
    items.push({ type: 'group', data: group });
  }
  if (ungroupedDownloads.value.length > 0) {
    items.push({ type: 'ungrouped', data: ungroupedDownloads.value });
  }
  return items;
});

const listAllPaginatedItems = computed(() => {
  const start = (listAllCurrentPage.value - 1) * pageSize.value;
  return listAllItems.value.slice(start, start + pageSize.value);
});

const listAllTotal = computed(() => listAllItems.value.length);

// 番剧视图分页
const groupPaginatedItems = computed(() => {
  const start = (groupCurrentPage.value - 1) * pageSize.value;
  return filteredGroups.value.slice(start, start + pageSize.value);
});

const groupTotal = computed(() => filteredGroups.value.length);

// 番剧详情弹窗分页
const detailPaginatedDownloads = computed(() => {
  if (!currentGroup.value) return [];
  const start = (detailCurrentPage.value - 1) * pageSize.value;
  return currentGroup.value.downloads.slice(start, start + pageSize.value);
});

const detailTotal = computed(() => currentGroup.value?.downloads?.length || 0);

// 切换页大小时重置页码
watch(pageSize, () => {
  listAllCurrentPage.value = 1;
  groupCurrentPage.value = 1;
  detailCurrentPage.value = 1;
});

// 搜索或切换tab时重置页码
watch(searchQuery, () => {
  listAllCurrentPage.value = 1;
  groupCurrentPage.value = 1;
});

// 打开番剧详情
const openGroupDetail = (group: any) => {
  currentGroup.value = group;
  detailCurrentPage.value = 1;
  groupDetailVisible.value = true;
};

// v3.5.2: 展开/收起合集
const toggleGroupExpand = (seriesName: string) => {
  const newSet = new Set(expandedGroups.value);
  if (newSet.has(seriesName)) {
    newSet.delete(seriesName);
  } else {
    newSet.add(seriesName);
  }
  expandedGroups.value = newSet;
};

// v3.5.2: 按 tab 过滤合集内的下载项
const filterDownloadsByTab = (downloads: any[]) => {
  if (activeTab.value === 'all') return downloads;
  const statusMap: Record<string, string[]> = {
    active: ['downloading', 'paused', 'pending'],
    completed: ['completed'],
    failed: ['error', 'cancelled']
  };
  const allowedStatuses = statusMap[activeTab.value] || [];
  return downloads.filter(dl => allowedStatuses.includes(dl.status));
};

// v3.5.2: 设为合集海报
const handleSetPoster = async (seriesName: string, videoId: string) => {
  isSettingPoster.value = videoId;
  try {
    const result = await ScrapeApi.setPoster(seriesName, videoId);
    if (result.status === 'success') {
      ElMessage.success(result.message);
      // 刷新分组数据以更新封面
      if (viewMode.value === 'group') await loadGroups();
    } else {
      ElMessage.error(result.message);
    }
  } catch (e) {
    ElMessage.error('设置合集海报失败');
  } finally {
    isSettingPoster.value = null;
  }
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

// 批量刮削（v3.3.9: 改为逐个刮削 + 进度反馈，避免单一请求超时且无反馈）
const handleBatchScrape = async () => {
  try {
    await ElMessageBox.confirm(
      '将对所有已下载的番剧目录生成NFO元数据文件（tvshow.nfo/movie.nfo）和封面图片，便于绿联NAS影视中心识别。是否继续？',
      '批量刮削',
      { confirmButtonText: '开始刮削', cancelButtonText: '取消', type: 'info' }
    );
  } catch { return; }

  // 先扫描可刮削的番剧列表
  let seriesList: string[] = [];
  try {
    const scrapable = await ScrapeApi.scanScrapableSeries();
    seriesList = scrapable.map(s => s.series_name);
  } catch (e) {
    ElMessage.error('扫描番剧列表失败');
    return;
  }

  if (seriesList.length === 0) {
    ElMessage.info('未发现可刮削的番剧目录');
    return;
  }

  // 重置进度状态
  batchScrapeProgress.value = {
    visible: true,
    running: true,
    total: seriesList.length,
    completed: 0,
    successCount: 0,
    failCount: 0,
    currentSeries: '',
    results: [],
    percentage: 0,
    status: ''
  };

  isBatchScraping.value = true;

  // 逐个刮削（避免单请求超时，可实时显示进度）
  for (const name of seriesList) {
    batchScrapeProgress.value.currentSeries = name;
    try {
      const result = await ScrapeApi.scrapeSeries({
        series_name: name,
        scrape_mode: 'tv_show',
        is_rename_file: true,
        is_reorganize_directory: true
      });
      batchScrapeProgress.value.results.push({
        series_name: name,
        is_success: result.is_success,
        error_message: result.error_message
      });
      if (result.is_success) {
        batchScrapeProgress.value.successCount++;
      } else {
        batchScrapeProgress.value.failCount++;
      }
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail || e?.message || '请求失败';
      batchScrapeProgress.value.results.push({
        series_name: name,
        is_success: false,
        error_message: errorMsg
      });
      batchScrapeProgress.value.failCount++;
    }
    batchScrapeProgress.value.completed++;
    batchScrapeProgress.value.percentage = Math.round(
      (batchScrapeProgress.value.completed / batchScrapeProgress.value.total) * 100
    );
  }

  // 完成
  batchScrapeProgress.value.running = false;
  batchScrapeProgress.value.currentSeries = '';
  if (batchScrapeProgress.value.failCount === 0) {
    batchScrapeProgress.value.status = 'success';
    ElMessage.success(`批量刮削完成: ${batchScrapeProgress.value.successCount} 个成功`);
  } else if (batchScrapeProgress.value.successCount === 0) {
    batchScrapeProgress.value.status = 'exception';
    ElMessage.error(`批量刮削失败: ${batchScrapeProgress.value.failCount} 个失败`);
  } else {
    batchScrapeProgress.value.status = 'warning';
    ElMessage.warning(`批量刮削部分成功: ${batchScrapeProgress.value.successCount} 成功, ${batchScrapeProgress.value.failCount} 失败`);
  }

  isBatchScraping.value = false;

  // 刷新分组视图（如果有）
  if (viewMode.value === 'group') await loadGroups();
};

// 修复NFO空标签（v3.3.9: 增加进度弹窗）
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

  // 重置进度状态
  fixNfoProgress.value = {
    visible: true,
    running: true,
    total: 0,
    fixed: 0,
    status: ''
  };

  isFixingNfo.value = true;
  try {
    const result = await ScrapeApi.fixNfoEmptyTags();
    fixNfoProgress.value.total = result.total;
    fixNfoProgress.value.fixed = result.fixed;
    if (result.fixed > 0) {
      fixNfoProgress.value.status = 'success';
      ElMessage.success(`修复完成: 扫描 ${result.total} 个 NFO，修复 ${result.fixed} 个文件`);
    } else {
      fixNfoProgress.value.status = 'success';
      ElMessage.success(`扫描 ${result.total} 个 NFO，无需修复`);
    }
  } catch (e) {
    fixNfoProgress.value.status = 'exception';
    ElMessage.error('修复 NFO 失败');
  } finally {
    fixNfoProgress.value.running = false;
    isFixingNfo.value = false;
  }
};

// 单个番剧刮削
const handleScrapeSeries = async (seriesName: string) => {
  isScrapingSingle.value = true;
  scrapingSeriesName.value = seriesName;
  try {
    const result = await ScrapeApi.scrapeSeries({
      series_name: seriesName,
      scrape_mode: 'tv_show',
      is_rename_file: true,
      is_reorganize_directory: true
    });
    if (result.is_success) {
      ElMessage.success(`刮削完成: ${seriesName}`);
      if (viewMode.value === 'group') await loadGroups();
    } else {
      ElMessage.error(`刮削失败: ${result.error_message || '未知错误'}`);
    }
  } catch (e) {
    ElMessage.error('刮削失败');
  } finally {
    isScrapingSingle.value = false;
    scrapingSeriesName.value = '';
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

// 合并系列相关状态
const mergeSeriesDialogVisible = ref(false);
const mergeSeriesNameInput = ref('');
const mergeSelectedDownloads = ref<any[]>([]);
const mergeSeasonNumbers = ref<number[]>([]);
const isMergingSeries = ref(false);
const mergeSelectTableRef = ref<any>(null);

// 已完成下载列表（用于合并选择）
const completedDownloadsList = computed(() => {
  return downloadStore.completedDownloads || [];
});

// 打开合并系列对话框
const openMergeSeriesDialog = () => {
  mergeSeriesDialogVisible.value = true;
  mergeSeriesNameInput.value = '';
  mergeSelectedDownloads.value = [];
  mergeSeasonNumbers.value = [];
};

// 处理合并选择变化
const handleMergeSelectionChange = (selection: any[]) => {
  mergeSelectedDownloads.value = selection;
  // 初始化季号数组
  mergeSeasonNumbers.value = selection.map((_, index) => {
    return mergeSeasonNumbers.value[index] || (index + 1);
  });
  // 如果只选了一个，自动用其 series_name 作为系列名称
  if (selection.length === 1 && selection[0].series_name) {
    mergeSeriesNameInput.value = selection[0].series_name;
  }
};

// 执行合并系列
const executeMergeSeries = async () => {
  if (mergeSelectedDownloads.value.length < 2) {
    ElMessage.warning('请至少选择两个番剧进行合并');
    return;
  }
  if (!mergeSeriesNameInput.value.trim()) {
    ElMessage.warning('请输入系列名称');
    return;
  }

  isMergingSeries.value = true;
  try {
    const items = mergeSelectedDownloads.value.map((dl, index) => ({
      video_id: dl.video_id,
      season_number: mergeSeasonNumbers.value[index] || (index + 1)
    }));

    const result = await DownloadApi.mergeSeries(mergeSeriesNameInput.value.trim(), items);
    if (result.status === 'success') {
      ElMessage.success(result.message || '合并成功');
      mergeSeriesDialogVisible.value = false;
      await downloadStore.initializeDownloads();
      if (viewMode.value === 'group') await loadGroups();
    } else {
      ElMessage.error(result.message || '合并失败');
    }
  } catch (error) {
    console.error('合并系列失败:', error);
    ElMessage.error('合并系列失败');
  } finally {
    isMergingSeries.value = false;
  }
};

// 初始化
onMounted(async () => {
  await downloadStore.initializeDownloads();
  // v3.5.2: 列表视图也需要分组数据
  await loadGroups();
  downloadStore.startPolling();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  downloadStore.stopPolling();
  downloadStore.disconnectWebSocket();
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

/* ========== v3.3.9: 批量刮削进度对话框 ========== */
.batch-progress-content {
  padding: 8px 4px;
}

.progress-summary {
  margin-bottom: 16px;
}

.progress-text {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary-color, #909399);
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-success {
  color: #67c23a;
  font-weight: 500;
}

.progress-fail {
  color: #f56c6c;
  font-weight: 500;
}

.progress-current {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  background-color: rgba(64, 158, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.15);
  border-radius: 8px;
  color: #409eff;
  font-size: 13px;
}

.progress-list {
  margin-top: 12px;
}

.progress-list-header {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-color, #303133);
}

.progress-list-body {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--border-color, #ebeef5);
  border-radius: 6px;
  padding: 4px 0;
}

.progress-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-color, #ebeef5);
}

.progress-list-item:last-child {
  border-bottom: none;
}

.progress-list-item.is-success {
  color: #67c23a;
}

.progress-list-item.is-fail {
  color: #f56c6c;
}

.progress-list-item .item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-list-item .item-error {
  font-size: 12px;
  opacity: 0.8;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fix-nfo-result {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background-color: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
}

:global(.light) .result-row {
  background-color: rgba(0, 0, 0, 0.03);
}

.result-label {
  font-size: 13px;
  color: var(--text-secondary-color, #909399);
}

.result-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #303133);
}

.result-value.has-fixed {
  color: #67c23a;
}

.progress-text {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary-color, #909399);
  text-align: center;
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

.page-size-label {
  font-size: 13px;
  color: var(--text-secondary-color);
  white-space: nowrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
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
  padding: 20px;
}

/* shimmer 动画 */
@keyframes skeleton-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton-shimmer {
  background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.04) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}
.skeleton-line {
  border-radius: 4px;
  background-color: rgba(255,255,255,0.06);
}

/* 分组骨架屏 */
.skeleton-group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.skeleton-group-card {
  background-color: rgba(255,255,255,0.06);
  border-radius: 12px;
  overflow: hidden;
}
.skeleton-group-cover {
  width: 100%;
  padding-top: 75%;
  background-color: rgba(255,255,255,0.04);
}
.skeleton-group-info {
  padding: 12px;
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

/* ========== v3.5.2: 列表可折叠合集 ========== */
.episode-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.collapsible-group-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.collapsible-group {
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  overflow: hidden;
}

.group-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.group-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.group-row-cover {
  width: 40px;
  height: 56px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.group-row-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.group-row-cover .blur-overlay,
.group-row-cover .hide-overlay {
  position: absolute;
  inset: 0;
}

.expand-icon {
  transition: transform 0.2s;
  flex-shrink: 0;
  color: var(--text-secondary-color, #909399);
}

.expand-icon.is-expanded {
  transform: rotate(90deg);
}

.group-row-info {
  flex: 1;
  min-width: 0;
}

.group-row-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.ungrouped-title {
  font-weight: 400;
  color: var(--text-secondary-color, #909399);
}

.group-row-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary-color, #909399);
  margin-top: 2px;
}

.group-row-actions {
  flex-shrink: 0;
}

.group-episodes {
  padding: 0 16px 8px 68px;
}

.episode-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
}

.episode-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.episode-row-cover {
  width: 30px;
  height: 42px;
  border-radius: 3px;
  overflow: hidden;
  flex-shrink: 0;
}

.episode-row-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.episode-row-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.episode-row-title {
  font-size: 14px;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.episode-row-size {
  font-size: 12px;
  color: var(--text-secondary-color, #909399);
  flex-shrink: 0;
}

.episode-row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
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

/* 合并系列对话框 */
.merge-series-dialog :deep(.el-dialog__header) {
  background-color: var(--bg-secondary-color);
  padding: 15px 20px;
}

.merge-series-dialog :deep(.el-dialog__title) {
  color: var(--text-color);
  font-size: 18px;
  font-weight: 600;
}

.merge-series-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: var(--text-secondary-color);
}

.merge-series-dialog :deep(.el-dialog__body) {
  background-color: var(--bg-color);
  padding: 20px;
}

.merge-series-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.merge-series-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background-color: var(--bg-secondary-color);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary-color);
}

.merge-series-hint .el-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.merge-series-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.merge-label {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
  white-space: nowrap;
}

.merge-select-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 12px;
}

.merge-select-table,
.merge-plan-table {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  /* v3.5.2: 平板端可折叠合集适配 */
  .group-row { padding: 10px 12px; }
  .group-episodes { padding: 0 12px 8px 56px; }
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
  /* 手机端每行2个按钮，6个按钮=3行（2+2+2） */
  .left-actions { grid-template-columns: repeat(2, 1fr); gap: 5px; }
  .right-actions { grid-template-columns: repeat(2, 1fr); gap: 5px; }
  .group-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .group-title { font-size: 13px; }
  /* v3.5.2: 手机端可折叠合集适配 */
  .group-row { padding: 8px 10px; gap: 8px; }
  .group-row-cover { width: 32px; height: 44px; }
  .group-row-title { font-size: 14px; }
  .group-row-meta { font-size: 11px; }
  .group-episodes { padding: 0 10px 6px 50px; }
  .episode-row { padding: 6px 8px; gap: 6px; }
  .episode-row-cover { width: 24px; height: 34px; }
  .episode-row-title { font-size: 13px; }
  .episode-row-actions { gap: 4px; }
  .episode-actions { gap: 4px; }
  .merge-series-name-row {
    flex-direction: column;
    align-items: stretch;
  }
  .merge-label {
    margin-bottom: 4px;
  }
}
</style>
