<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">设置</h1>
    </div>

    <div class="settings-container">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>下载设置</span>
          </div>
        </template>
        <el-form :model="downloadForm" label-width="120px">
          <el-form-item label="下载目录">
            <div class="download-dir-row">
              <el-input
                v-model="downloadForm.downloadPath"
                placeholder="输入绝对路径，Docker环境: /app/downloads，本地: D:\Downloads"
              >
                <template #append>
                  <el-button @click="openDownloadDir" title="打开目录">
                    <el-icon><FolderOpened /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>
          </el-form-item>
        </el-form>
        <div class="card-footer">
          <el-button type="primary" @click="saveDownloadDir">保存设置</el-button>
          <el-button @click="openDownloadDir">
            <el-icon><FolderOpened /></el-icon> 打开目录
          </el-button>
        </div>
        <div class="download-dir-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>每部番剧将自动创建以番剧名命名的文件夹，视频和封面保存在同一文件夹内</span>
        </div>
        <div class="download-dir-hint docker-hint">
          <el-icon><Warning /></el-icon>
          <span>Docker 环境下仅支持 Linux 格式路径，且只能访问容器内或已挂载的目录。如需保存到宿主机，请在 docker-compose.yml 中添加卷挂载（如 - /your/host/path:/data/downloads），然后设置路径为 /data/downloads</span>
        </div>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>代理设置</span>
          </div>
        </template>
        <el-form :model="proxyForm" label-width="120px">
          <el-form-item label="使用代理">
            <el-switch
              v-model="proxyForm.useProxy"
              @change="handleProxyChange"
            />
          </el-form-item>
          <el-form-item label="代理地址" :disabled="!proxyForm.useProxy">
            <el-input
              v-model="proxyForm.proxyUrl"
              placeholder="例如: localhost:7890"
              :disabled="!proxyForm.useProxy"
              @blur="handleProxyUrlBlur"
            />
          </el-form-item>
          <div class="proxy-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>Docker 环境下如需代理宿主机本地服务，请使用 <code>host.docker.internal</code> 代替 <code>127.0.0.1</code>，例如：<code>http://host.docker.internal:7890</code></span>
          </div>
        </el-form>
        <div class="card-footer">
          <el-button type="primary" @click="saveProxySettings">保存设置</el-button>
          <el-button
            :loading="testingProxy"
            :disabled="!proxyForm.useProxy || !proxyForm.proxyUrl"
            @click="testProxyConnection"
          >
            <el-icon><Connection /></el-icon> 测试代理
          </el-button>
        </div>
        
        <div v-if="proxyTestResult" class="proxy-test-result" :class="{ success: proxyTestResult.success, error: !proxyTestResult.success }">
          <el-icon v-if="proxyTestResult.success"><CircleCheck /></el-icon>
          <el-icon v-else><CircleClose /></el-icon>
          <span>{{ proxyTestResult.message }}</span>
          <span v-if="proxyTestResult.latency_ms" class="latency">延迟: {{ proxyTestResult.latency_ms }}ms</span>
        </div>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>数据管理</span>
          </div>
        </template>
        <div class="data-actions">
          <el-button type="danger" plain @click="showClearDialog = true">
            <el-icon><Delete /></el-icon> 清空所有本地数据
          </el-button>
          <el-button @click="exportData">
            <el-icon><Download /></el-icon> 导出数据
          </el-button>
          <el-button @click="importData">
            <el-icon><Upload /></el-icon> 导入数据
          </el-button>
        </div>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>内容屏蔽</span>
          </div>
        </template>
        <el-form :model="contentForm" label-width="120px">
          <el-form-item label="屏蔽敏感图片">
            <el-switch
              v-model="contentForm.enableBlur"
              @change="handleBlurChange"
            />
          </el-form-item>
          <el-form-item label="屏蔽方式" :disabled="!contentForm.enableBlur">
            <el-select
              v-model="contentForm.blurMode"
              :disabled="!contentForm.enableBlur"
              style="width: 100%;"
            >
              <el-option label="毛玻璃打码" value="blur" />
              <el-option label="不显示图片" value="hide" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="card-footer">
          <el-button type="primary" @click="saveContentSettings">保存设置</el-button>
        </div>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>账号安全</span>
          </div>
        </template>
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="120px">
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input
              v-model="passwordForm.oldPassword"
              type="password"
              show-password
              placeholder="请输入旧密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              show-password
              placeholder="请输入新密码（至少6位）"
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入新密码"
            />
          </el-form-item>
        </el-form>
        <div class="card-footer">
          <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">保存密码</el-button>
        </div>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>关于</span>
          </div>
        </template>
        <div class="about-info">
          <p><strong>版本:</strong> v2.3.1</p>
          <p><strong>描述:</strong> Hanime视频聚合平台</p>
          <p><strong>功能:</strong> 视频浏览、收藏、下载、播放清单</p>
          <p><strong>更新日志:</strong> <a href="/changelog" class="changelog-link">查看更新记录</a></p>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="showClearDialog"
      title="清空数据"
      width="30%"
    >
      <span>确定要清空所有本地数据吗？此操作将清除收藏、稍后观看、播放清单和观看历史，且不可撤销。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showClearDialog = false">取消</el-button>
          <el-button type="danger" @click="handleClearData">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <input
      ref="fileInputRef"
      type="file"
      accept=".json"
      class="hidden-input"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { AccountApi } from '../api/account';
import request from '../utils/request';
import { Delete, Download, Upload, Connection, CircleCheck, CircleClose, FolderOpened, InfoFilled, Warning } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { useContentSettings } from '../composables/useContentSettings';

interface ProxySettings {
  use_proxy: boolean;
  proxy_url: string;
}

interface ProxyTestResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}

const proxyForm = reactive({
  useProxy: false,
  proxyUrl: ''
});

const { enableBlur: contentEnableBlur, blurMode: contentBlurMode, setEnableBlur, setBlurMode } = useContentSettings();

const contentForm = reactive({
  enableBlur: true,
  blurMode: 'blur' as 'blur' | 'hide'
});

const showClearDialog = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const testingProxy = ref(false);
const proxyTestResult = ref<ProxyTestResult | null>(null);

const downloadForm = reactive({
  downloadPath: ''
});

// 修改密码表单
const passwordFormRef = ref<FormInstance | null>(null);
const changingPassword = ref(false);
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const validateConfirmPassword = (_rule: any, value: string, callback: Function) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const passwordRules = reactive<FormRules>({
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
});

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return;
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return;
    changingPassword.value = true;
    try {
      const result = await AccountApi.changePassword(passwordForm.oldPassword, passwordForm.newPassword);
      if (result.success) {
        ElMessage.success('密码修改成功');
        passwordForm.oldPassword = '';
        passwordForm.newPassword = '';
        passwordForm.confirmPassword = '';
        passwordFormRef.value?.resetFields();
      } else {
        ElMessage.error(result.message || '密码修改失败');
      }
    } catch (error: any) {
      ElMessage.error(error?.response?.data?.message || '密码修改失败');
    } finally {
      changingPassword.value = false;
    }
  });
};

const loadSettings = async () => {
  try {
    const response = await request.get<ProxySettings>('/settings/proxy');
    proxyForm.useProxy = response.data.use_proxy;
    proxyForm.proxyUrl = response.data.proxy_url || '';
  } catch (error) {
    console.error('加载代理设置失败:', error);
    const useProxy = localStorage.getItem('useProxy');
    const proxyUrl = localStorage.getItem('proxyUrl');
    proxyForm.useProxy = useProxy === 'true';
    proxyForm.proxyUrl = proxyUrl || '';
  }
  
  contentForm.enableBlur = contentEnableBlur.value;
  contentForm.blurMode = contentBlurMode.value;
};

const handleProxyChange = () => {
  if (!proxyForm.useProxy) {
    proxyForm.proxyUrl = '';
  }
};

const handleBlurChange = () => {
  if (!contentForm.enableBlur) {
    contentForm.blurMode = 'blur';
  }
};

const saveContentSettings = () => {
  setEnableBlur(contentForm.enableBlur);
  setBlurMode(contentForm.blurMode);
  ElMessage.success('设置已保存');
};

const handleProxyUrlBlur = () => {
  if (!proxyForm.proxyUrl) return;
  if (!proxyForm.proxyUrl.startsWith('http://') && !proxyForm.proxyUrl.startsWith('https://')) {
    proxyForm.proxyUrl = 'http://' + proxyForm.proxyUrl;
  }
};

const saveProxySettings = async () => {
  try {
    const response = await request.put('/settings/proxy', {
      use_proxy: proxyForm.useProxy,
      proxy_url: proxyForm.proxyUrl
    });
    if (response.data.success) {
      ElMessage.success('设置已保存');
      localStorage.setItem('useProxy', proxyForm.useProxy.toString());
      localStorage.setItem('proxyUrl', proxyForm.proxyUrl);
      if (response.data.restart_required) {
        ElMessage.info('代理状态已更改，部分功能可能需要刷新页面');
      }
    } else {
      ElMessage.error(response.data.message || '保存失败');
    }
  } catch (error) {
    console.error('保存代理设置失败:', error);
    ElMessage.error('保存失败');
  }
};

const testProxyConnection = async () => {
  if (!proxyForm.useProxy || !proxyForm.proxyUrl) {
    ElMessage.warning('请先启用代理并填写代理地址');
    return;
  }

  testingProxy.value = true;
  proxyTestResult.value = null;

  try {
    const response = await request.get('/settings/proxy/test');
    proxyTestResult.value = response.data;
    if (response.data.success) {
      ElMessage.success('代理测试成功！');
    } else {
      ElMessage.error(`代理测试失败: ${response.data.message}`);
    }
  } catch (error) {
    console.error('测试代理失败:', error);
    proxyTestResult.value = {
      success: false,
      message: '测试请求失败，请检查网络连接'
    };
    ElMessage.error('测试代理失败');
  } finally {
    testingProxy.value = false;
  }
};

const handleClearData = async () => {
  showClearDialog.value = false;
  try {
    await AccountApi.clearWatchHistory();
    const favorites = await AccountApi.getFavorites();
    for (const f of favorites) {
      await AccountApi.removeFavorite(f.video_id);
    }
    const watchLater = await AccountApi.getWatchLater();
    for (const w of watchLater) {
      await AccountApi.removeWatchLater(w.video_id);
    }
    const playlists = await AccountApi.getPlaylists();
    for (const p of playlists) {
      await AccountApi.deletePlaylist(p.playlist_id);
    }
    ElMessage.success('已清空所有数据');
  } catch (error) {
    console.error('清空数据失败:', error);
    ElMessage.error('清空数据失败');
  }
};

const exportData = async () => {
  try {
    const data = {
      favorites: await AccountApi.getFavorites(),
      watchLater: await AccountApi.getWatchLater(),
      playlists: await AccountApi.getPlaylists(),
      history: await AccountApi.getWatchHistory(),
      exportTime: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `hanime_data_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    ElMessage.success('数据导出成功');
  } catch (error) {
    console.error('导出数据失败:', error);
    ElMessage.error('导出数据失败');
  }
};

const importData = () => {
  fileInputRef.value?.click();
};

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  try {
    const text = await file.text();
    const data = JSON.parse(text);

    if (data.favorites) {
      for (const f of data.favorites) {
        await AccountApi.addFavorite(f.video_id, f.title, f.cover_url);
      }
    }
    if (data.watchLater) {
      for (const w of data.watchLater) {
        await AccountApi.addWatchLater(w.video_id, w.title, w.cover_url);
      }
    }
    if (data.playlists) {
      for (const p of data.playlists) {
        const playlist = await AccountApi.createPlaylist(p.name);
        for (const v of p.videos) {
          await AccountApi.addVideoToPlaylist(playlist.playlist_id, v.video_id, v.title, v.cover_url);
        }
      }
    }
    if (data.history) {
      for (const h of data.history) {
        await AccountApi.addWatchHistory(h.video_id, h.title, h.cover_url, h.progress || 0, h.duration || '');
      }
    }

    ElMessage.success('数据导入成功');
  } catch (error) {
    console.error('导入数据失败:', error);
    ElMessage.error('导入数据失败，请确保文件格式正确');
  }

  target.value = '';
};

onMounted(() => {
  loadSettings();
  loadDownloadDir();
});

const loadDownloadDir = async () => {
  try {
    const response = await request.get('/settings/download-dir');
    downloadForm.downloadPath = response.data.download_path;
  } catch (error) {
    console.error('加载下载目录设置失败:', error);
  }
};

const selectDownloadDir = () => {
  // 不再需要 - 直接在输入框编辑
};

const openDownloadDir = async () => {
  try {
    const response = await request.post('/settings/open-dir');
    if (response.data.success) {
      ElMessage.success(`目录路径: ${response.data.path}`);
    } else {
      ElMessage.warning(response.data.message || '无法打开目录，请手动访问: ' + downloadForm.downloadPath);
    }
  } catch (error) {
    ElMessage.info('下载目录: ' + downloadForm.downloadPath);
  }
};

const saveDownloadDir = async () => {
  if (!downloadForm.downloadPath.trim()) {
    ElMessage.warning('请输入下载目录路径');
    return;
  }
  try {
    const response = await request.put('/settings/download-dir', {
      download_path: downloadForm.downloadPath.trim()
    });
    if (response.data.success) {
      ElMessage.success('下载目录已更新');
      downloadForm.downloadPath = response.data.download_path;
    } else {
      ElMessage.error(response.data.message || '更新失败');
    }
  } catch (error) {
    console.error('保存下载目录失败:', error);
    ElMessage.error('保存下载目录失败');
  }
};
</script>

<style scoped>
.settings-page {
  width: 100%;
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.settings-container {
  max-width: 600px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.card-footer {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.data-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.about-info {
  font-size: 14px;
  color: var(--text-secondary-color);
}

.about-info p {
  margin: 8px 0;
}

.changelog-link {
  color: var(--primary-color);
  text-decoration: none;
}

.changelog-link:hover {
  text-decoration: underline;
}

.hidden-input {
  display: none;
}

.download-dir-row {
  width: 100%;
}

.download-dir-hint {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.download-dir-hint.docker-hint {
  background-color: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  margin-top: 8px;
}

.proxy-hint {
  margin-top: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  background-color: rgba(64, 158, 255, 0.1);
  color: var(--text-secondary-color);
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.6;
}

.proxy-hint code {
  background-color: rgba(255, 255, 255, 0.15);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}

.proxy-test-result {
  margin-top: 15px;
  padding: 12px 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.proxy-test-result.success {
  background-color: rgba(25, 135, 84, 0.1);
  color: #198754;
}

.proxy-test-result.error {
  background-color: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.proxy-test-result .latency {
  margin-left: auto;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .settings-page {
    padding: 10px;
  }

  .page-title {
    font-size: 20px;
  }

  .settings-container {
    max-width: 100%;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .settings-page {
    padding: 5px;
  }

  .page-title {
    font-size: 18px;
  }

  :deep(.el-form-item__label) {
    width: 80px !important;
    font-size: 12px;
  }

  .card-footer {
    flex-wrap: wrap;
    gap: 8px;
  }

  .download-dir-hint,
  .proxy-hint {
    font-size: 11px;
  }

  .data-actions {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .data-actions .el-button {
    flex: 1;
    min-width: 0;
  }
}
</style>
