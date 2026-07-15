import { ref, computed, watch } from 'vue';
import request from '../utils/request';

const enableBlur = ref<boolean | null>(null);
const blurMode = ref<'blur' | 'hide' | null>(null);
let isInitialized = false;
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
    } else {
      enableBlur.value = true;
      blurMode.value = 'blur';
    }
  } catch (error) {
    console.error('获取用户设置失败:', error);
    enableBlur.value = true;
    blurMode.value = 'blur';
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
      blurMode: blurMode.value
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

export function useContentSettings() {
  // 确保 fetch 只执行一次
  if (!isInitialized) {
    isInitialized = true;
    fetchSettings();
  }

  const shouldBlur = computed(() => enableBlur.value === true);
  const mode = computed(() => (blurMode.value || 'blur') as 'blur' | 'hide');

  const setEnableBlur = (val: boolean) => {
    enableBlur.value = val;
  };

  const setBlurMode = (val: 'blur' | 'hide') => {
    blurMode.value = val;
  };

  const refreshSettings = () => {
    fetchSettings();
  };

  return {
    shouldBlur,
    mode,
    enableBlur: computed(() => enableBlur.value === true),
    blurMode: computed(() => (blurMode.value || 'blur') as 'blur' | 'hide'),
    setEnableBlur,
    setBlurMode,
    refreshSettings
  };
}
