import { ref, computed, watch, onMounted } from 'vue';
import request from '../utils/request';

const enableBlur = ref<boolean>(true);
const blurMode = ref<'blur' | 'hide'>('blur');

const fetchSettings = async () => {
  try {
    const response = await request.get('/accounts/me/settings');
    if (response.data && response.data.success && response.data.settings) {
      const settings = response.data.settings;
      if (settings.enableBlur !== undefined) {
        enableBlur.value = settings.enableBlur;
      }
      if (settings.blurMode === 'hide' || settings.blurMode === 'blur') {
        blurMode.value = settings.blurMode;
      }
    }
  } catch (error) {
    console.error('获取用户设置失败:', error);
  }
};

const saveSettings = async () => {
  try {
    await request.post('/accounts/me/settings', {
      enableBlur: enableBlur.value,
      blurMode: blurMode.value
    });
  } catch (error) {
    console.error('保存用户设置失败:', error);
  }
};

watch(enableBlur, async () => {
  await saveSettings();
});

watch(blurMode, async () => {
  await saveSettings();
});

onMounted(() => {
  fetchSettings();
});

export function useContentSettings() {
  const shouldBlur = computed(() => enableBlur.value);
  const mode = computed(() => blurMode.value);

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
    enableBlur,
    blurMode,
    setEnableBlur,
    setBlurMode,
    refreshSettings
  };
}