/**
 * 版本号统一管理 composable（v3.3.9 新增）
 *
 * 从后端 /settings/version 接口动态获取版本号，避免前端硬编码。
 * 多个组件共用同一份缓存，避免重复请求。
 */
import { ref } from 'vue';
import request from '../utils/request';

// 全局缓存（多组件共享）
const version = ref<string>('0.0.0');
const appName = ref<string>('');
const appDescription = ref<string>('');
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
    }
  } catch (error) {
    console.error('获取版本信息失败:', error);
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

export function useVersion() {
  // 第一次调用时触发获取
  if (!isFetched && !isFetching) {
    fetchVersion();
  }

  return {
    version,
    appName,
    appDescription,
    prefixedVersion,
    refreshVersion
  };
}
