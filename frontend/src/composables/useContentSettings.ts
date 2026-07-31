import { ref, computed, watch } from 'vue';
import request from '../utils/request';

const enableBlur = ref<boolean | null>(null);
const blurMode = ref<'blur' | 'hide' | null>(null);
// v3.5.3: 是否显示发行商
const showStudio = ref<boolean | null>(null);
let isFetching = false;

const fetchSettings = async () => {
  if (isFetching) return;
  isFetching = true;
  try {
    const response = await request.get('/accounts/me/settings');
    if (response.data && response.data.success && response.data.settings) {
      const settings = response.data.settings;
      if (settings.enableBlur !== undefined) {
        enableBlur.value = settings.enableBlur;
      } else {
        enableBlur.value = true;
      }
      if (settings.blurMode === 'hide' || settings.blurMode === 'blur') {
        blurMode.value = settings.blurMode;
      } else {
        blurMode.value = 'blur';
      }
      // v3.5.3: 读取 showStudio 设置
      if (settings.showStudio !== undefined) {
        showStudio.value = settings.showStudio;
      } else {
        showStudio.value = true;
      }
    } else {
      enableBlur.value = true;
      blurMode.value = 'blur';
      showStudio.value = true;
    }
  } catch (error) {
    console.error('获取用户设置失败:', error);
    enableBlur.value = true;
    blurMode.value = 'blur';
    showStudio.value = true;
  } finally {
    isFetching = false;
  }
};

let saveTimer: ReturnType<typeof setTimeout> | null = null;
const saveSettings = async () => {
  if (enableBlur.value === null || blurMode.value === null) return;
  try {
    await request.post('/accounts/me/settings', {
      enableBlur: enableBlur.value,
      blurMode: blurMode.value,
      showStudio: showStudio.value
    });
  } catch (error) {
    console.error('保存用户设置失败:', error);
  }
};

// 防抖保存，避免 fetchSettings 触发 watch 导致循环
const debouncedSave = () => {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(saveSettings, 300);
};

watch(enableBlur, (newVal, oldVal) => {
  if (oldVal === null) return; // 初始化赋值时不保存
  debouncedSave();
});

watch(blurMode, (newVal, oldVal) => {
  if (oldVal === null) return;
  debouncedSave();
});

// v3.5.3: showStudio 变化时自动保存
watch(showStudio, (newVal, oldVal) => {
  if (oldVal === null) return;
  debouncedSave();
});

// 监听登录/登出事件，重新获取设置
if (typeof window !== 'undefined') {
  window.addEventListener('user-login', () => {
    fetchSettings();
  });
  window.addEventListener('user-logout', () => {
    // 登出时重置为默认值
    enableBlur.value = true;
    blurMode.value = 'blur';
    showStudio.value = true;
  });
  // 监听 storage 事件（跨标签页切换登录时同步）
  window.addEventListener('storage', (e) => {
    if (e.key === 'token') {
      if (e.newValue) {
        // 新登录，重新获取设置
        fetchSettings();
      } else {
        // 登出
        enableBlur.value = true;
        blurMode.value = 'blur';
        showStudio.value = true;
      }
    }
  });
}

export function useContentSettings() {
  // 每次调用都确保设置已加载
  // 如果值为null（尚未初始化），触发获取
  if (enableBlur.value === null) {
    fetchSettings();
  }

  const shouldBlur = computed(() => enableBlur.value === true);
  const mode = computed(() => (blurMode.value || 'blur') as 'blur' | 'hide');
  const shouldShowStudio = computed(() => showStudio.value === true);

  const setEnableBlur = (val: boolean) => {
    enableBlur.value = val;
  };

  const setBlurMode = (val: 'blur' | 'hide') => {
    blurMode.value = val;
  };

  const setShowStudio = (val: boolean) => {
    showStudio.value = val;
  };

  const refreshSettings = () => {
    fetchSettings();
  };

  return {
    shouldBlur,
    mode,
    shouldShowStudio,
    enableBlur: computed(() => enableBlur.value === true),
    blurMode: computed(() => (blurMode.value || 'blur') as 'blur' | 'hide'),
    setEnableBlur,
    setBlurMode,
    setShowStudio,
    refreshSettings
  };
}
