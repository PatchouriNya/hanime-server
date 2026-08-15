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
    const response = await request.post('/accounts/me/favorites', null, {
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
    const response = await request.post('/accounts/me/watch_later', null, {
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
    const response = await request.post('/accounts/me/playlists', null, {
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
    const response = await request.post(`/accounts/me/playlists/${playlist_id}/videos`, null, {
      params: { video_id, title, cover_url }
    });
    return response.data;
  }

  static async removeVideoFromPlaylist(playlist_id: string, video_id: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/playlists/${playlist_id}/videos/${video_id}`);
    return response.data;
  }

  static async updatePlaylistName(playlist_id: string, name: string): Promise<VideoActionResponse> {
    const response = await request.put(`/accounts/me/playlists/${playlist_id}`, null, {
      params: { name }
    });
    return response.data;
  }

  static async moveVideoToPlaylist(from_playlist_id: string, to_playlist_id: string, video_id: string): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/playlists/move-video', null, {
      params: { from_playlist_id, to_playlist_id, video_id }
    });
    return response.data;
  }

  static async getWatchHistory(): Promise<WatchHistoryItem[]> {
    const response = await request.get('/accounts/me/history');
    return response.data.history || [];
  }

  static async addWatchHistory(video_id: string, title: string, cover_url: string, progress: number = 0, duration: string = ''): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/history', null, {
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

  static async changePassword(oldPassword: string, newPassword: string): Promise<{success: boolean; message: string}> {
    const response = await request.put('/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    });
    return response.data;
  }

  // ==================== 番剧追更订阅（v4.0.0） ====================

  static async getSubscriptions(): Promise<string[]> {
    const response = await request.get('/accounts/me/subscriptions');
    return response.data.subscriptions || [];
  }

  static async addSubscription(seriesName: string): Promise<VideoActionResponse> {
    const response = await request.post('/accounts/me/subscriptions', null, {
      params: { series_name: seriesName }
    });
    return response.data;
  }

  static async removeSubscription(seriesName: string): Promise<VideoActionResponse> {
    const response = await request.delete(`/accounts/me/subscriptions/${encodeURIComponent(seriesName)}`);
    return response.data;
  }

  // 检查订阅系列是否有新集（返回系列名 + has_new + 最新集信息）
  static async checkSubscriptions(): Promise<any[]> {
    const response = await request.get('/accounts/me/subscriptions/check');
    return response.data.results || [];
  }

  // ==================== v4.0.0: 用户信息与管理（管理员） ====================

  static async getMe(): Promise<{ username: string; user_type: number; is_admin: boolean; db_type: string }> {
    const response = await request.get('/auth/me');
    return response.data;
  }

  static async listUsers(): Promise<any[]> {
    const response = await request.get('/users');
    return response.data.users || [];
  }

  static async createUser(username: string, password: string, userType: number = 10): Promise<any> {
    const response = await request.post('/users', { username, password, user_type: userType });
    return response.data;
  }

  static async deleteUser(username: string): Promise<any> {
    const response = await request.delete(`/users/${encodeURIComponent(username)}`);
    return response.data;
  }

  static async resetUserPassword(username: string, newPassword: string): Promise<any> {
    const response = await request.put(`/users/${encodeURIComponent(username)}/password`, { new_password: newPassword });
    return response.data;
  }

  static async updateUserStatus(username: string, userStatus: number): Promise<any> {
    const response = await request.put(`/users/${encodeURIComponent(username)}/status`, { status: userStatus });
    return response.data;
  }

  static async updateUserRole(username: string, userType: number): Promise<any> {
    const response = await request.put(`/users/${encodeURIComponent(username)}/role`, { user_type: userType });
    return response.data;
  }
}
