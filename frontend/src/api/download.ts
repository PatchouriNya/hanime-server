import request from '../utils/request.ts';
import { DownloadProgress, DownloadActionType } from '../types/download';

/**
 * 下载相关API服务
 */
export const DownloadApi = {
  /**
   * 获取下载历史
   */
  getDownloadHistory: async (search?: string, status?: string): Promise<DownloadProgress[]> => {
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (status) params.status = status;
      const response = await request.get<DownloadProgress[]>('/downloads/history', { params });
      return response.data;
    } catch (error) {
      console.error('获取下载历史失败:', error);
      return [];
    }
  },

  /**
   * 获取按番剧分组的下载列表
   */
  getDownloadGroups: async (): Promise<any[]> => {
    try {
      const response = await request.get('/downloads/groups');
      return response.data;
    } catch (error) {
      console.error('获取下载分组失败:', error);
      return [];
    }
  },

  /**
   * 扫描下载目录恢复记录
   */
  scanAndRestore: async (): Promise<any> => {
    try {
      const response = await request.post('/downloads/scan');
      return response.data;
    } catch (error) {
      console.error('扫描恢复失败:', error);
      return { restored: [], errors: ['请求失败'], total_restored: 0 };
    }
  },

  /**
   * 清除已完成的下载记录（不删除文件）
   */
  clearCompleted: async (): Promise<any> => {
    try {
      const response = await request.post('/downloads/action', {
        video_id: '',
        action: 'clear_completed'
      });
      return response.data;
    } catch (error) {
      console.error('清除已完成记录失败:', error);
      return { status: 'error', message: '操作失败' };
    }
  },

  /**
   * 清除失败的下载记录
   */
  clearFailed: async (): Promise<any> => {
    try {
      const response = await request.post('/downloads/action', {
        video_id: '',
        action: 'clear_failed'
      });
      return response.data;
    } catch (error) {
      console.error('清除失败记录失败:', error);
      return { status: 'error', message: '操作失败' };
    }
  },

  /**
   * 开始下载视频
   * @param videoId 视频ID
   * @param force 是否强制重新下载
   */
  startDownload: async (videoId: string, force: boolean = false) => {
    try {
      const response = await request.post('/downloads/start', {
        video_id: videoId,
        force
      });
      return response.data;
    } catch (error) {
      console.error('开始下载失败:', error);
      return { status: 'error', message: '开始下载失败' };
    }
  },

  /**
   * 执行下载操作 (暂停/继续/取消/重试/删除)
   * @param videoId 视频ID
   * @param action 操作类型
   */
  handleDownloadAction: async (videoId: string, action: DownloadActionType) => {
    try {
      const response = await request.post('/downloads/action', {
        video_id: videoId,
        action
      });
      return response.data;
    } catch (error) {
      console.error(`${action}操作失败:`, error);
      return { status: 'error', message: `${action}操作失败` };
    }
  },

  /**
   * 获取API基础URL
   * @returns 返回API基础URL，如果是相对路径则返回完整URL
   */
  getBaseUrl: (): string => {
    const baseURL = request.defaults.baseURL || '';
    // 如果是相对路径，转换为绝对路径
    if (baseURL.startsWith('/')) {
      const protocol = window.location.protocol;
      const host = window.location.host;
      return `${protocol}//${host}${baseURL}`;
    }
    return baseURL;
  },

  /**
   * 获取已下载视频的访问链接
   * @param videoId 视频ID
   */
  getVideoFileUrl: (videoId: string): string => {
    return `/api/downloads/file/${videoId}`;
  },

  /**
   * 获取封面URL
   * 统一通过本地API获取，后端会自动处理：
   * - 如果本地存在，直接返回
   * - 如果不存在，实时下载后返回
   * @param videoId 视频ID
   */
  getCoverUrl: (videoId: string): string => {
    const token = localStorage.getItem('token');
    return `/api/downloads/cover/${videoId}${token ? `?token=${token}` : ''}`;
  },

  /**
   * 创建WebSocket连接以接收下载进度更新
   * @param onMessage 消息处理函数
   */
  createWebSocket: (onMessage: (data: DownloadProgress) => void): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsPath = `${protocol}//${host}/api/downloads/ws`;

    const ws = new WebSocket(wsPath);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as DownloadProgress;
        onMessage(data);
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
    
    return ws;
  },
  
  /**
   * 格式化文件大小
   * @param bytes 字节数
   */
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
  
  /**
   * 格式化下载速度
   * @param bytesPerSecond 每秒字节数
   */
  formatSpeed: (bytesPerSecond: number): string => {
    return `${DownloadApi.formatFileSize(bytesPerSecond)}/s`;
  }
}; 