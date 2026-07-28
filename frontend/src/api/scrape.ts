import request from '../utils/request';

export type ScrapeMode = 'tv_show' | 'movie';

export interface ScrapeConfig {
  scrape_mode: ScrapeMode;
  is_auto_scrape: boolean;
  is_rename_file: boolean;
  is_reorganize_directory: boolean;
  is_convert_cover_to_jpg: boolean;
  is_generate_fanart: boolean;
  // v3.3.9 新增：翻译设置
  is_translate_plot_enabled: boolean;
  translate_target_lang: string; // 'zh-CN' | 'ja' | 'en' | 'off'
}

export interface ScrapeRequest {
  series_name: string;
  scrape_mode: ScrapeMode;
  is_rename_file: boolean;
  is_reorganize_directory: boolean;
}

export interface ScrapeResult {
  series_name: string;
  scrape_mode: ScrapeMode;
  nfo_files: string[];
  image_files: string[];
  renamed_files: string[];
  is_success: boolean;
  error_message?: string;
}

export interface ScrapableSeries {
  series_name: string;
  video_count: number;
  has_nfo: boolean;
  has_poster: boolean;
  video_files: string[];
}

export interface NfoPreview {
  series_name: string;
  scrape_mode: ScrapeMode;
  tvshow_nfo?: string;
  episode_nfos: { filename: string; content: string }[];
  movie_nfo?: string;
  rename_mapping: { original: string; new: string }[];
}

export class ScrapeApi {
  static async getConfig(): Promise<ScrapeConfig> {
    const response = await request.get('/scrape/config');
    return response.data;
  }

  static async updateConfig(config: ScrapeConfig): Promise<any> {
    const response = await request.put('/scrape/config', config);
    return response.data;
  }

  static async scrapeSeries(req: ScrapeRequest): Promise<ScrapeResult> {
    // 单个番剧刮削需要下载多个封面和元数据，使用 5 分钟超时
    const response = await request.post('/scrape/series', req, { timeout: 300000 });
    return response.data;
  }

  static async batchScrape(
    seriesNames: string[],
    mode: ScrapeMode = 'tv_show',
    isRenameFile: boolean = true,
    isReorganizeDirectory: boolean = true
  ): Promise<ScrapeResult[]> {
    // 批量刮削耗时较长（每个番剧需要下载多个封面/元数据），使用 10 分钟超时
    const response = await request.post(
      '/scrape/batch',
      {
        series_names: seriesNames,
        scrape_mode: mode,
        is_rename_file: isRenameFile,
        is_reorganize_directory: isReorganizeDirectory
      },
      { timeout: 600000 }
    );
    return response.data;
  }

  static async previewScrape(seriesName: string): Promise<NfoPreview> {
    const response = await request.get(`/scrape/preview/${encodeURIComponent(seriesName)}`);
    return response.data;
  }

  static async scanScrapableSeries(): Promise<ScrapableSeries[]> {
    const response = await request.get('/scrape/scan');
    return response.data;
  }

  static async fixNfoEmptyTags(): Promise<{ total: number; fixed: number }> {
    // 扫描所有 NFO 文件可能耗时较长（番剧很多时），使用 5 分钟超时
    const response = await request.post('/scrape/fix-nfo', {}, { timeout: 300000 });
    return response.data;
  }

  // v3.5.2 新增：将指定剧集的封面设为合集海报
  static async setPoster(seriesName: string, videoId: string): Promise<{ status: string; message: string }> {
    const response = await request.post('/scrape/set-poster', {
      series_name: seriesName,
      video_id: videoId
    });
    return response.data;
  }
}
