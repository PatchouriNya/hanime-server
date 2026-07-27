/**
 * 版本号统一管理 composable（v3.3.9 新增）
 *
 * 从后端 /settings/version 接口动态获取版本号，避免前端硬编码。
 * 多个组件共用同一份缓存，避免重复请求。
 * 使用 localStorage 缓存，页面加载时立即显示，后台静默更新。
 */
import { ref } from 'vue';
import request from '../utils/request';

const CACHE_KEY = 'ld_app_version';

// 从 localStorage 恢复缓存，避免 v0.0.0 闪烁
const _loadCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
      const data = JSON.parse(cached);
      return {
        version: data.version || '0.0.0',
        appName: data.app_name || '',
        appDescription: data.app_description || ''
      };
    }
  } catch { /* ignore */ }
  return null;
};

const _saveCache = (ver: string, name: string, desc: string) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      version: ver,
      app_name: name,
      app_description: desc
    }));
  } catch { /* ignore */ }
};

// 优先用缓存，无缓存时才用默认值
const _cached = _loadCache();

const version = ref<string>(_cached?.version || '0.0.0');
const appName = ref<string>(_cached?.appName || '');
const appDescription = ref<string>(_cached?.appDescription || '');
let isFetched = false;
let isFetching = false;

const fetchVersion = async () => {
  if (isFetching || isFetched) return;
  isFetching = true;
  try {
    const response = await request.get('/settings/version');
    if (response.data) {
      version.value = response.data.version || '0.0.0';
      appName.value = response.data.app_name || '';
      appDescription.value = response.data.app_description || '';
      isFetched = true;
      // 持久化到 localStorage，下次加载秒开
      _saveCache(version.value, appName.value, appDescription.value);
    }
  } catch (error) {
    // 静默失败，不影响用户体验
  } finally {
    isFetching = false;
  }
};

// 带前缀的版本号（如 "v3.3.9"）
const prefixedVersion = () => `v${version.value}`;

// 强制刷新（用于刷新后版本号变化）
const refreshVersion = async () => {
  isFetched = false;
  await fetchVersion();
};

/**
 * 从外部数据更新版本信息（如首页数据中携带的版本号）
 * 避免单独发 /settings/version 请求
 */
const updateFromExternal = (data: { version?: string; app_name?: string; app_description?: string }) => {
  if (data?.version) {
    version.value = data.version;
    appName.value = data.app_name || appName.value;
    appDescription.value = data.app_description || appDescription.value;
    isFetched = true;
    _saveCache(version.value, appName.value, appDescription.value);
  }
};

export function useVersion() {
  // 第一次调用时触发后台获取（不阻塞渲染，因已有缓存兜底）
  if (!isFetched && !isFetching) {
    fetchVersion();
  }

  return {
    version,
    appName,
    appDescription,
    prefixedVersion,
    refreshVersion,
    updateFromExternal
  };
}
