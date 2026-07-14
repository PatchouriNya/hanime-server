import request from '../utils/request';

export interface UserVideoItem {
  video_id: string;
  title: string;
  cover_url: string;
  added_at: string;
}

export interface UserPlaylist {
  playlist_id: string;
  name: string;
  videos: UserVideoItem[];
  created_at: string;
  updated_at: string;
}

export interface WatchHistoryItem extends UserVideoItem {
  progress: number;
  duration: string;
}

export interface VideoActionResponse {
  success: boolean;
  message: string;
}

export class AccountApi {
  static async getFavorites(): Promise<UserVideoItem[]> {
    const response = await request.get('/accounts/me/favorites');
    return response.data.favorites || [];
  }

  static async addFavorite(video_id: string, title: string, cover_url: string): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/favorites', {
      params: { video_id, title, cover_url }
    });
    return response.data;
  }

  static async removeFavorite(video_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/favorites/${video_id}`);
    return response.data;
  }

  static async isFavorite(video_id: string): Promise<boolean> {
    const response = await request.get(`/accounts/me/favorites/${video_id}`);
    return response.data.is_favorite || false;
  }

  static async getWatchLater(): Promise<UserVideoItem[]> {
    const response = await request.get('/accounts/me/watch_later');
    return response.data.watch_later || [];
  }

  static async addWatchLater(video_id: string, title: string, cover_url: string): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/watch_later', {
      params: { video_id, title, cover_url }
    });
    return response.data;
  }

  static async removeWatchLater(video_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/watch_later/${video_id}`);
    return response.data;
  }

  static async isWatchLater(video_id: string): Promise<boolean> {
    const response = await request.get(`/accounts/me/watch_later/${video_id}`);
    return response.data.is_watch_later || false;
  }

  static async getPlaylists(): Promise<UserPlaylist[]> {
    const response = await request.get('/accounts/me/playlists');
    return response.data.playlists || [];
  }

  static async createPlaylist(name: string): Promise<UserPlaylist> {
    const response = await request.post('/accounts/me/playlists', {
      params: { name }
    });
    return response.data.playlist;
  }

  static async deletePlaylist(playlist_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/playlists/${playlist_id}`);
    return response.data;
  }

  static async getPlaylist(playlist_id: string): Promise<UserPlaylist> {
    const response = await request.get(`/accounts/me/playlists/${playlist_id}`);
    return response.data.playlist;
  }

  static async addVideoToPlaylist(playlist_id: string, video_id: string, title: string, cover_url: string): Promise<VideoActionResponse> {
    const response = await request.post(`/accounts/me/playlists/${playlist_id}/videos`, {
      params: { video_id, title, cover_url }
    });
    return response.data;
  }

  static async removeVideoFromPlaylist(playlist_id: string, video_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/playlists/${playlist_id}/videos/${video_id}`);
    return response.data;
  }

  static async updatePlaylistName(playlist_id: string, name: string): Promise<VideoActionResponse> {
    const response = await request.put(`/accounts/me/playlists/${playlist_id}`, {
      params: { name }
    });
    return response.data;
  }

  static async getWatchHistory(): Promise<WatchHistoryItem[]> {
    const response = await request.get('/accounts/me/history');
    return response.data.history || [];
  }

  static async addWatchHistory(video_id: string, title: string, cover_url: string, progress: number = 0, duration: string = ''): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/history', {
      params: { video_id, title, cover_url, progress, duration }
    });
    return response.data;
  }

  static async clearWatchHistory(): Promise<VideoActionResponse> {
    const response = await request.delete('/accounts/me/history');
    return response.data;
  }

  static async removeWatchHistory(video_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/history/${video_id}`);
    return response.data;
  }
}
