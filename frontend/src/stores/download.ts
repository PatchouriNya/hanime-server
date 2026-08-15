import { defineStore } from 'pinia';
import { DownloadApi } from '../api/download';
import type { DownloadProgress } from '../types/download';
import { ElMessage, ElNotification } from 'element-plus';

/**
 * WebSocket管理类 - 单例模式
 */
class DownloadWebSocketManager {
  private static instance: DownloadWebSocketManager;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout = 2000;
  private listeners: Set<(data: any) => void> = new Set();
  private isConnecting = false;
  
  private constructor() {
    // 私有构造函数确保单例

    // 页面可见性变化时智能连接或断开
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        // 页面重新可见，如果有监听器则重连
        if (this.listeners.size > 0) {
          this.connect();
        }
      } else {
        // 页面不可见，断开 WebSocket 节省资源
        this.close();
      }
    });

    // 窗口关闭前优雅地关闭连接
    window.addEventListener('beforeunload', () => {
      this.close();
    });
  }
  
  static getInstance(): DownloadWebSocketManager {
    if (!this.instance) {
      this.instance = new DownloadWebSocketManager();
    }
    return this.instance;
  }
  
  connect(): void {
    // 避免重复连接
    if (this.ws || this.isConnecting) {
      return;
    }
    
    this.isConnecting = true;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/downloads/ws`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.isConnecting = false;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notifyListeners(data);
        } catch (error) {
          // 消息解析失败，静默处理
        }
      };

      this.ws.onerror = () => {
        // wss:// 连接失败通常是外层反向代理未配置 WebSocket Upgrade，静默处理
        this.isConnecting = false;
      };

      this.ws.onclose = () => {
        this.ws = null;
        this.isConnecting = false;

        // 尝试重连（降低次数，避免控制台反复报错）
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
          }, this.reconnectTimeout * Math.min(this.reconnectAttempts, 5));
        }
      };
    } catch (error) {
      // 创建连接失败，静默处理
      this.isConnecting = false;

      // 连接失败后稍后重试
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, this.reconnectTimeout * Math.min(this.reconnectAttempts, 5));
    }
  }
  
  addListener(callback: (data: any) => void): void {
    this.listeners.add(callback);
    
    // 如果添加监听器时没有连接，则自动连接
    if (!this.ws && !this.isConnecting) {
      this.connect();
    }
  }
  
  removeListener(callback: (data: any) => void): void {
    this.listeners.delete(callback);
  }
  
  private notifyListeners(data: any): void {
    this.listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('WebSocket监听器处理失败:', error);
      }
    });
  }
  
  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnecting = false;
    }
  }
}

// 新增：下载速度平滑处理类
class DownloadSpeedSmoother {
  private static instance: DownloadSpeedSmoother;
  private speedHistory: Map<string, number[]> = new Map(); // 下载ID -> 历史速度值
  private lastUpdateTime: Map<string, number> = new Map(); // 下载ID -> 上次更新时间
  private historySize = 5; // 保留的历史数据点数量
  private speedCalculator: Map<string, {prevBytes: number, prevTime: number, speed: number}> = new Map();
  
  private constructor() {
    // 私有构造函数确保单例
  }
  
  static getInstance(): DownloadSpeedSmoother {
    if (!this.instance) {
      this.instance = new DownloadSpeedSmoother();
    }
    return this.instance;
  }
  
  // 平滑处理下载速度
  smoothSpeed(videoId: string, reportedSpeed: number, downloaded: number): number {
    const now = Date.now();
    
    // 初始化历史数据
    if (!this.speedHistory.has(videoId)) {
      this.speedHistory.set(videoId, []);
      this.lastUpdateTime.set(videoId, now);
      this.speedCalculator.set(videoId, {
        prevBytes: downloaded,
        prevTime: now,
        speed: reportedSpeed
      });
    }
    
    // 获取历史数据
    const history = this.speedHistory.get(videoId)!;
    const lastUpdate = this.lastUpdateTime.get(videoId)!;
    const calculator = this.speedCalculator.get(videoId)!;
    
    // 如果距离上次更新时间超过100ms，计算实际速度并更新
    if (now - lastUpdate > 100) {
      const timeDiff = now - calculator.prevTime;
      if (timeDiff > 0 && downloaded > calculator.prevBytes) {
        const bytesDiff = downloaded - calculator.prevBytes;
        const actualSpeed = (bytesDiff / timeDiff) * 1000; // 转换为每秒字节数
        
        // 添加到历史数据
        history.push(actualSpeed);
        // 限制历史数据大小
        if (history.length > this.historySize) {
          history.shift();
        }
        
        // 更新计算器数据
        calculator.prevBytes = downloaded;
        calculator.prevTime = now;
        
        // 计算加权平均速度 (最近的数据权重更高)
        let totalWeight = 0;
        let weightedSum = 0;
        
        for (let i = 0; i < history.length; i++) {
          const weight = i + 1;
          weightedSum += history[i] * weight;
          totalWeight += weight;
        }
        
        const smoothedSpeed = weightedSum / totalWeight;
        calculator.speed = smoothedSpeed;
      }
      
      this.lastUpdateTime.set(videoId, now);
    }
    
    // 如果服务器报告速度为0但有下载进度，使用上次计算的速度
    if (reportedSpeed === 0 && calculator.speed > 0) {
      return calculator.speed;
    }
    
    // 使用计算出的平滑速度或服务器报告的速度
    return calculator.speed > 0 ? calculator.speed : reportedSpeed;
  }
  
  // 清除特定下载的历史数据
  clearHistory(videoId: string): void {
    this.speedHistory.delete(videoId);
    this.lastUpdateTime.delete(videoId);
    this.speedCalculator.delete(videoId);
  }
}

// WebSocket 兜底轮询定时器（模块级变量，避免响应式序列化问题）
let _pollTimer: ReturnType<typeof setInterval> | null = null;

// 速度平滑处理器（模块级单例，避免放入响应式 state 导致类型推断失败）
const _speedSmoother = DownloadSpeedSmoother.getInstance();

// v3.6.3 修复：保存已绑定的 WS 进度监听器引用。
// 此前 connectWebSocket 用 addListener(this.updateDownloadProgress.bind(this)) 注册，
// disconnectWebSocket 却用 removeListener(this.updateDownloadProgress.bind(this)) 移除——
// 两次 bind 产生不同函数引用，removeListener 永远匹配不上，监听器随连接/断开反复累积。
// 现在连接时保存绑定引用，断开时用同一引用移除。
let _wsProgressListener: ((data: any) => void) | null = null;

// v4.0.0: 下载完成通知去重（每次会话内同一视频只通知一次，避免轮询/WS 重复触发）
const _notifiedCompletedIds = new Set<string>();

const _notifyDownloadCompleted = (progress: DownloadProgress) => {
  if (_notifiedCompletedIds.has(progress.video_id)) return;
  _notifiedCompletedIds.add(progress.video_id);
  ElNotification({
    title: '下载完成',
    message: progress.title || progress.filename || progress.video_id,
    type: 'success',
    duration: 5000,
    position: 'bottom-right'
  });
};

/**
 * 下载状态Store
 */
export const useDownloadStore = defineStore('download', {
  state: () => ({
    downloads: {} as Record<string, DownloadProgress>,
    wsConnected: false,
    lastUpdated: 0,
    isLoading: false,
    // 批量删除模式
    batchDeleteMode: false,
    // 已选中的下载项ID
    selectedDownloads: new Set<string>()
  }),
  
  getters: {
    // 所有下载
    allDownloads: (state) => Object.values(state.downloads),
    
    // 活跃下载（下载中、暂停、等待中）
    activeDownloads: (state) => Object.values(state.downloads).filter(
      download => ['downloading', 'paused', 'pending'].includes(download.status)
    ),
    
    // 已完成下载
    completedDownloads: (state) => Object.values(state.downloads).filter(
      download => download.status === 'completed'
    ),
    
    // 失败的下载
    failedDownloads: (state) => Object.values(state.downloads).filter(
      download => download.status === 'error' || download.status === 'cancelled'
    ),
    
    // 暂停的下载
    pausedDownloads: (state) => Object.values(state.downloads).filter(
      download => download.status === 'paused'
    ),
    
    // 总下载速度
    totalDownloadSpeed: (state) => {
      return Object.values(state.downloads)
        .filter(download => download.status === 'downloading')
        .reduce((total, download) => total + (download.speed || 0), 0);
    },
    
    // 总下载大小
    totalSize: (state) => {
      return Object.values(state.downloads)
        .reduce((total, download) => total + (download.total_size || 0), 0);
    },
    
    // 已下载总大小
    totalDownloaded: (state) => {
      return Object.values(state.downloads)
        .reduce((total, download) => total + (download.downloaded || 0), 0);
    },
    
    // 是否有活跃下载
    hasActiveDownloads: (state) => {
      return Object.values(state.downloads).some(
        download => download.status === 'downloading' || download.status === 'pending'
      );
    },
    
    // 是否有暂停的下载
    hasPausedDownloads: (state) => {
      return Object.values(state.downloads).some(
        download => download.status === 'paused'
      );
    },
    
    // 新增：是否有选中的下载项
    hasSelectedDownloads: (state) => state.selectedDownloads.size > 0,
    
    // 新增：选中的下载项数量
    selectedDownloadsCount: (state) => state.selectedDownloads.size,
    
    // 新增：获取当前选中的下载项
    selectedDownloadItems: (state) => {
      return Object.values(state.downloads).filter(download => 
        state.selectedDownloads.has(download.video_id)
      );
    }
  },
  
  actions: {
    /**
     * 初始化下载列表和WebSocket连接
     */
    async initializeDownloads() {
      this.isLoading = true;
      
      try {
        // 从API获取下载历史（始终刷新，不跳过）
        const history = await DownloadApi.getDownloadHistory();
        
        // 初始化状态
        history.forEach(item => {
          const existing = this.downloads[item.video_id];
          if (existing && existing.status === 'downloading' && existing.speed > 0) {
            return; // 保留 WebSocket 实时进度
          }
          this.downloads[item.video_id] = item;
        });
        
        // 初始化WebSocket连接（仅当未连接时）
        if (!this.wsConnected) {
          this.connectWebSocket();
        }
      } catch (error) {
        console.error('加载下载历史失败:', error);
        ElMessage.error('加载下载历史失败');
      } finally {
        this.isLoading = false;
      }

      this.lastUpdated = Date.now();
    },

    /**
     * 刷新下载列表（不检查是否已初始化）
     */
    async refreshDownloads() {
      try {
        const history = await DownloadApi.getDownloadHistory();
        // 保留正在进行的下载的实时进度
        history.forEach(item => {
          const existing = this.downloads[item.video_id];
          if (existing && existing.status === 'downloading' && existing.speed > 0) {
            // 保留 WebSocket 推送的实时进度，不覆盖
            return;
          }
          this.downloads[item.video_id] = item;
        });
        // 移除已不在历史中的条目
        const historyIds = new Set(history.map(item => item.video_id));
        for (const id of Object.keys(this.downloads)) {
          if (!historyIds.has(id)) {
            delete this.downloads[id];
          }
        }
        // 确保WebSocket连接（如果断开则重连）
        if (!this.wsConnected) {
          this.connectWebSocket();
        }
      } catch (error) {
        console.error('刷新下载列表失败:', error);
      }
      this.lastUpdated = Date.now();
    },

    /**
     * 启动智能轮询：
     * - 有活跃下载时：每 5 秒轮询一次（兜底 WebSocket）
     * - 无活跃下载时：停止轮询，由 WebSocket 推送驱动
     */
    startPolling() {
      if (_pollTimer) return;
      const poll = () => {
        // 没有活跃下载 → 停止轮询，等 WebSocket 推送触发
        if (!this.hasActiveDownloads && !this.hasPausedDownloads) {
          this.stopPolling();
          return;
        }
        this.refreshDownloads();
      };
      _pollTimer = setInterval(poll, 5000);
      // 立即执行一次
      poll();
    },

    /**
     * 停止周期性轮询
     */
    stopPolling() {
      if (_pollTimer) {
        clearInterval(_pollTimer);
        _pollTimer = null;
      }
    },

    /**
     * 建立WebSocket连接，接收实时下载进度更新
     */
    connectWebSocket() {
      // 如果已经连接，则不重复连接
      if (this.wsConnected) {
        return;
      }

      const wsManager = DownloadWebSocketManager.getInstance();
      // 复用已绑定的监听器引用，保证 disconnect 时能正确移除
      if (!_wsProgressListener) {
        _wsProgressListener = this.updateDownloadProgress.bind(this);
      }
      wsManager.addListener(_wsProgressListener);
      wsManager.connect();
      this.wsConnected = true;
    },

    /**
     * 断开WebSocket连接（离开下载页时调用）
     */
    disconnectWebSocket() {
      const wsManager = DownloadWebSocketManager.getInstance();
      if (_wsProgressListener) {
        wsManager.removeListener(_wsProgressListener);
        _wsProgressListener = null;
      }
      wsManager.close();
      this.wsConnected = false;
    },
    
    /**
     * 更新下载进度
     */
    updateDownloadProgress(progress: DownloadProgress) {
      const existingDownload = this.downloads[progress.video_id];

      // 应用速度平滑处理
      if (progress.status === 'downloading') {
        // 平滑处理下载速度
        const smoothedSpeed = _speedSmoother.smoothSpeed(
          progress.video_id,
          progress.speed,
          progress.downloaded
        );

        // 使用平滑后的速度值
        progress.speed = smoothedSpeed;
      } else if (['completed', 'cancelled', 'error'].includes(progress.status)) {
        // 当下载结束时，清除历史数据
        _speedSmoother.clearHistory(progress.video_id);
        // 所有下载完成后停止轮询
        if (!this.hasActiveDownloads) {
          this.stopPolling();
        }
      }
      
      // 如果状态变化需要特殊处理
      if (existingDownload && existingDownload.status !== progress.status) {
        // 处理状态转换特殊情况
        if (progress.status === 'completed' && existingDownload.status === 'downloading') {
          // 下载刚完成，记录最终速度为0
          progress.speed = 0;
          // v4.0.0: 下载完成通知（每次会话只通知一次）
          _notifyDownloadCompleted(progress);
        }
      }
      
      // 更新下载数据
      this.downloads[progress.video_id] = progress;
      
      // 更新最后更新时间
      this.lastUpdated = Date.now();
    },
    
    /**
     * 开始下载视频
     */
    async startDownload(videoId: string, force: boolean = false) {
      try {
        const result = await DownloadApi.startDownload(videoId, force);

        if (result.status === 'success') {
          // 主动刷新下载列表，确保新下载项立即显示
          this.refreshDownloads();
          // 新下载开始，确保轮询已启动
          this.startPolling();
          return true;
        } else if (result.status === 'warning' && result.existing_download) {
          // 视频已经下载过，询问用户
          return result;
        } else {
          ElMessage.error(result.message || '开始下载失败');
          return false;
        }
      } catch (error) {
        console.error('开始下载失败:', error);
        ElMessage.error('开始下载失败');
        return false;
      }
    },
    
    /**
     * 暂停下载
     */
    async pauseDownload(videoId: string) {
      try {
        const result = await DownloadApi.handleDownloadAction(videoId, 'pause');
        if (result.status === 'success') {
          return true;
        } else {
          ElMessage.error(result.message || '暂停下载失败');
          return false;
        }
      } catch (error) {
        console.error('暂停下载失败:', error);
        ElMessage.error('暂停下载失败');
        return false;
      }
    },
    
    /**
     * 恢复下载
     */
    async resumeDownload(videoId: string) {
      try {
        const result = await DownloadApi.handleDownloadAction(videoId, 'resume');
        if (result.status === 'success') {
          return true;
        } else {
          ElMessage.error(result.message || '恢复下载失败');
          return false;
        }
      } catch (error) {
        console.error('恢复下载失败:', error);
        ElMessage.error('恢复下载失败');
        return false;
      }
    },
    
    /**
     * 取消下载
     */
    async cancelDownload(videoId: string) {
      try {
        const result = await DownloadApi.handleDownloadAction(videoId, 'cancel');
        if (result.status === 'success') {
          // 等待一段时间确保后端处理完成
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // 强制更新一次本地状态
          if (videoId in this.downloads) {
            this.downloads[videoId].status = 'cancelled';
            _speedSmoother.clearHistory(videoId);
          }
          
          return true;
        } else {
          ElMessage.error(result.message || '取消下载失败');
          return false;
        }
      } catch (error) {
        console.error('取消下载失败:', error);
        ElMessage.error('取消下载失败');
        return false;
      }
    },
    
    /**
     * 重试下载
     */
    async retryDownload(videoId: string) {
      try {
        const result = await DownloadApi.handleDownloadAction(videoId, 'retry');
        if (result.status === 'success') {
          return true;
        } else {
          ElMessage.error(result.message || '重试下载失败');
          return false;
        }
      } catch (error) {
        console.error('重试下载失败:', error);
        ElMessage.error('重试下载失败');
        return false;
      }
    },
    
    /**
     * 删除下载记录
     * @param videoId 视频ID
     * @param deleteFiles 是否删除源文件（视频+刮削文件），默认 true
     */
    async deleteDownload(videoId: string, deleteFiles: boolean = true) {
      try {
        const result = await DownloadApi.handleDownloadAction(videoId, 'delete', deleteFiles);
        if (result.status === 'success') {
          delete this.downloads[videoId];
          return true;
        } else {
          ElMessage.error(result.message || '删除下载失败');
          return false;
        }
      } catch (error) {
        console.error('删除下载失败:', error);
        ElMessage.error('删除下载失败');
        return false;
      }
    },
    
    /**
     * 暂停所有下载
     */
    async pauseAllDownloads() {
      const downloadingIds = this.activeDownloads
        .filter(d => d.status === 'downloading')
        .map(d => d.video_id);
      
      if (downloadingIds.length === 0) {
        ElMessage.info('没有正在下载的任务');
        return false;
      }
      
      let success = true;
      
      for (const id of downloadingIds) {
        const result = await this.pauseDownload(id);
        if (!result) success = false;
      }
      return success;
    },
    
    /**
     * 恢复所有下载
     */
    async resumeAllDownloads() {
      const pausedIds = this.pausedDownloads.map(d => d.video_id);
      
      if (pausedIds.length === 0) {
        ElMessage.info('没有已暂停的下载');
        return false;
      }
      
      let success = true;
      
      for (const id of pausedIds) {
        const result = await this.resumeDownload(id);
        if (!result) success = false;
      }
      return success;
    },
    
    /**
     * 清除已完成的下载记录
     */
    async clearCompletedDownloads() {
      const completedIds = this.completedDownloads.map(d => d.video_id);
      
      if (completedIds.length === 0) {
        ElMessage.info('没有已完成的下载');
        return false;
      }
      
      let success = true;
      
      for (const id of completedIds) {
        const result = await this.deleteDownload(id);
        if (!result) success = false;
      }
      
      if (success) {
        ElMessage.success('已清除所有已完成的下载');
      }
      
      return success;
    },
    
    /**
     * 清除失败的下载记录
     */
    async clearFailedDownloads() {
      const failedIds = this.failedDownloads.map(d => d.video_id);
      
      if (failedIds.length === 0) {
        ElMessage.info('没有失败的下载');
        return false;
      }
      
      let success = true;
      
      for (const id of failedIds) {
        const result = await this.deleteDownload(id);
        if (!result) success = false;
      }
      
      if (success) {
        ElMessage.success('已清除所有失败的下载');
      }
      
      return success;
    },
    
    /**
     * 重试所有失败的下载
     */
    async retryAllFailedDownloads() {
      const errorIds = this.failedDownloads
        .filter(d => d.status === 'error')
        .map(d => d.video_id);
      
      if (errorIds.length === 0) {
        ElMessage.info('没有失败的下载可重试');
        return false;
      }
      
      let success = true;
      
      for (const id of errorIds) {
        const result = await this.retryDownload(id);
        if (!result) success = false;
      }
      
      if (success) {
        ElMessage.success('已重试所有失败的下载');
      }
      
      return success;
    },
    
    /**
     * 获取格式化的总体进度
     */
    getOverallProgress() {
      const total = this.totalSize;
      const downloaded = this.totalDownloaded;
      
      if (total === 0) return 0;
      return Math.min(100, Math.round((downloaded / total) * 100));
    },
    
    // 是否已下载某视频
    isDownloaded(videoId: string): boolean {
      const item = this.downloads[videoId];
      return !!item && item.status === 'completed';
    },
    
    /**
     * 切换批量删除模式
     */
    toggleBatchDeleteMode() {
      this.batchDeleteMode = !this.batchDeleteMode;
      if (!this.batchDeleteMode) {
        // 退出批量删除模式时清空选择
        this.clearSelection();
      }
    },
    
    /**
     * 选择/取消选择下载项
     */
    toggleSelection(videoId: string) {
      if (this.selectedDownloads.has(videoId)) {
        this.selectedDownloads.delete(videoId);
      } else {
        this.selectedDownloads.add(videoId);
      }
    },
    
    /**
     * 全选当前过滤条件下的下载项
     */
    selectAll(downloadItems: DownloadProgress[]) {
      downloadItems.forEach(item => {
        this.selectedDownloads.add(item.video_id);
      });
    },
    
    /**
     * 取消全选
     */
    clearSelection() {
      this.selectedDownloads.clear();
    },
    
    /**
     * 批量删除选中的下载项
     * @param deleteFiles 是否删除源文件（视频+刮削文件），默认 true
     */
    async deleteSelected(deleteFiles: boolean = true) {
      if (this.selectedDownloads.size === 0) return false;

      try {
        const videoIds = Array.from(this.selectedDownloads);
        const result = await DownloadApi.batchDelete(videoIds, deleteFiles);

        if (result.status === 'success') {
          // 从内存中移除已删除的记录（仅移除成功的，保留失败的）
          const failedIds = new Set(result.failed_ids || []);
          videoIds.forEach(id => {
            if (!failedIds.has(id)) {
              delete this.downloads[id];
            }
          });

          const successCount = result.success_count || 0;
          const failedCount = result.failed_count || 0;
          if (failedCount > 0) {
            ElMessage.warning(`成功删除 ${successCount} 条，失败 ${failedCount} 条`);
            // 仅清除成功的选中项
            videoIds.forEach(id => {
              if (!failedIds.has(id)) {
                this.selectedDownloads.delete(id);
              }
            });
          } else {
            ElMessage.success(result.message || `已删除 ${successCount} 个下载记录`);
            this.clearSelection();
            // 退出批量删除模式
            this.batchDeleteMode = false;
          }
          return true;
        } else {
          ElMessage.error(result.message || '批量删除失败');
          return false;
        }
      } catch (error) {
        console.error('批量删除失败:', error);
        ElMessage.error('批量删除失败，请稍后重试');
        return false;
      }
    },
    
    /**
     * 检查下载项是否被选中
     */
    isSelected(videoId: string) {
      return this.selectedDownloads.has(videoId);
    }
  }
}); 