<template>
  <div class="users-page">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <p class="page-subtitle">管理用户账号与权限</p>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 添加用户
        </el-button>
        <el-button @click="loadUsers" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-spinner :size="48" />
    </div>

    <div v-else class="users-table-wrap">
      <el-table :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.user_type >= 20 ? 'warning' : 'info'" size="small">
              {{ row.user_type >= 20 ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="150">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="300">
          <template #default="{ row }">
            <el-button
              v-if="row.username !== currentUsername"
              size="small"
              @click="openRoleDialog(row)"
            >
              {{ row.user_type >= 20 ? '设为普通用户' : '设为管理员' }}
            </el-button>
            <el-button
              v-if="row.username !== currentUsername"
              size="small"
              @click="openResetDialog(row)"
            >
              重置密码
            </el-button>
            <el-button
              v-if="row.username !== currentUsername"
              size="small"
              :type="row.status === 10 ? 'warning' : 'success'"
              plain
              @click="toggleStatus(row)"
            >
              {{ row.status === 10 ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="row.username !== currentUsername"
              size="small"
              type="danger"
              plain
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加用户 -->
    <el-dialog v-model="createDialogVisible" title="添加用户" :width="isMobile ? '90%' : '420px'">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" placeholder="至少3位" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="createForm.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="createForm.user_type">
            <el-radio :value="10">普通用户</el-radio>
            <el-radio :value="20">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" :width="isMobile ? '90%' : '420px'">
      <p class="dialog-tip">为用户 <strong>{{ resetTarget?.username }}</strong> 设置新密码</p>
      <el-input v-model="resetPassword" type="password" show-password placeholder="新密码（至少6位）" />
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="handleReset">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { AccountApi } from '../api/account';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh } from '@element-plus/icons-vue';

const router = useRouter();
const loading = ref(false);
const users = ref<any[]>([]);
const currentUsername = ref('');
const isMobile = ref(window.innerWidth <= 768);

const createDialogVisible = ref(false);
const createForm = ref({ username: '', password: '', user_type: 10 });
const creating = ref(false);

const resetDialogVisible = ref(false);
const resetTarget = ref<any>(null);
const resetPassword = ref('');
const resetting = ref(false);

const getStatusType = (status: number): 'success' | 'warning' | 'danger' | 'info' => {
  if (status === 10) return 'success';
  if (status === 20) return 'warning';
  return 'danger';
};

const getStatusText = (status: number): string => {
  const map: Record<number, string> = { 10: '正常', 20: '禁用', 30: '封禁' };
  return map[status] || String(status);
};

const formatTime = (value: string): string => {
  if (!value) return '';
  const date = new Date(value);
  if (isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

const loadUsers = async () => {
  loading.value = true;
  try {
    users.value = await AccountApi.listUsers();
  } catch (error: any) {
    console.error('加载用户列表失败:', error);
    if (error?.response?.status === 403) {
      ElMessage.error('需要管理员权限');
      router.push('/');
      return;
    }
    ElMessage.error('加载用户列表失败');
  } finally {
    loading.value = false;
  }
};

const openCreateDialog = () => {
  createForm.value = { username: '', password: '', user_type: 10 };
  createDialogVisible.value = true;
};

const handleCreate = async () => {
  if (createForm.value.username.length < 3 || createForm.value.password.length < 6) {
    ElMessage.warning('用户名至少3位，密码至少6位');
    return;
  }
  creating.value = true;
  try {
    await AccountApi.createUser(createForm.value.username, createForm.value.password, createForm.value.user_type);
    ElMessage.success('用户创建成功');
    createDialogVisible.value = false;
    await loadUsers();
  } catch (error) {
    console.error('创建用户失败:', error);
    ElMessage.error('创建用户失败（用户名可能已存在）');
  } finally {
    creating.value = false;
  }
};

const openResetDialog = (row: any) => {
  resetTarget.value = row;
  resetPassword.value = '';
  resetDialogVisible.value = true;
};

const handleReset = async () => {
  if (!resetTarget.value) return;
  if (resetPassword.value.length < 6) {
    ElMessage.warning('密码至少6位');
    return;
  }
  resetting.value = true;
  try {
    await AccountApi.resetUserPassword(resetTarget.value.username, resetPassword.value);
    ElMessage.success('密码已重置');
    resetDialogVisible.value = false;
  } catch (error) {
    console.error('重置密码失败:', error);
    ElMessage.error('重置密码失败');
  } finally {
    resetting.value = false;
  }
};

const openRoleDialog = async (row: any) => {
  const newType = row.user_type >= 20 ? 10 : 20;
  const action = newType === 20 ? '设为管理员' : '设为普通用户';
  try {
    await ElMessageBox.confirm(`确定将「${row.username}」${action}吗？`, '修改角色', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
  } catch {
    return;
  }
  try {
    await AccountApi.updateUserRole(row.username, newType);
    ElMessage.success('角色已更新');
    await loadUsers();
  } catch (error) {
    console.error('更新角色失败:', error);
    ElMessage.error('更新角色失败');
  }
};

const toggleStatus = async (row: any) => {
  const newStatus = row.status === 10 ? 20 : 10;
  try {
    await ElMessageBox.confirm(
      `确定要${newStatus === 20 ? '禁用' : '启用'}用户「${row.username}」吗？`,
      '修改状态',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    );
  } catch {
    return;
  }
  try {
    await AccountApi.updateUserStatus(row.username, newStatus);
    ElMessage.success('状态已更新');
    await loadUsers();
  } catch (error) {
    console.error('更新状态失败:', error);
    ElMessage.error('更新状态失败');
  }
};

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${row.username}」吗？此操作不可恢复。`,
      '删除用户',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    );
  } catch {
    return;
  }
  try {
    await AccountApi.deleteUser(row.username);
    ElMessage.success('用户已删除');
    await loadUsers();
  } catch (error) {
    console.error('删除用户失败:', error);
    ElMessage.error('删除用户失败');
  }
};

onMounted(async () => {
  try {
    const me = await AccountApi.getMe();
    currentUsername.value = me.username;
    if (!me.is_admin) {
      ElMessage.warning('需要管理员权限');
      router.push('/');
      return;
    }
    await loadUsers();
  } catch (error) {
    console.error('获取用户信息失败:', error);
    router.push('/');
  }
});
</script>

<style scoped>
.users-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary-color);
  margin: 4px 0 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.dialog-tip {
  margin: 0 0 12px;
  color: var(--text-color);
  font-size: 14px;
}

@media (min-width: 769px) {
  .users-page {
    padding: 32px 28px;
  }

  .page-title {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .users-page {
    padding: 10px;
  }

  .users-table-wrap {
    overflow-x: auto;
  }
}
</style>
