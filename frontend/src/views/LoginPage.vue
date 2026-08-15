<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" class="logo-icon"><Star /></el-icon>
          <span class="logo-text">Hanime</span>
        </div>
        <h1 class="login-title">欢迎回来</h1>
        <p class="login-subtitle">请登录以继续使用</p>
      </div>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
        <el-form-item>
          <div class="db-type-selector">
            <button
              type="button"
              class="db-type-btn"
              :class="{ active: dbType === 'local' }"
              @click="dbType = 'local'"
            >
              <el-icon :size="16"><Monitor /></el-icon>
              <span>本地数据库</span>
            </button>
            <button
              type="button"
              class="db-type-btn"
              :class="{ active: dbType === 'cloud' }"
              @click="dbType = 'cloud'"
            >
              <el-icon :size="16"><Cloudy /></el-icon>
              <span>云数据库</span>
            </button>
          </div>
        </el-form-item>

        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            @keyup.enter="handleArrowRight"
            class="login-input"
          >
            <template #prefix>
              <el-icon class="input-icon"><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            @keyup.enter="handleArrowRight"
            class="login-input"
            show-password
          >
            <template #prefix>
              <el-icon class="input-icon"><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleArrowRight"
          >
            <el-icon><ArrowRight /></el-icon>
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <div class="remember-row">
          <el-checkbox v-model="rememberUsername" class="remember-checkbox">记住账号</el-checkbox>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">
        <el-icon><CircleClose /></el-icon>
        <span>{{ errorMessage }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Star, User, Lock, ArrowRight, CircleClose, Monitor, Cloudy } from '@element-plus/icons-vue';
import { useRouter, useRoute } from 'vue-router';
import request from '../utils/request';

const router = useRouter();
const route = useRoute();

const loginFormRef = ref();

const loginForm = reactive({
  username: '',
  password: ''
});

const loading = ref(false);
const errorMessage = ref('');
const rememberUsername = ref(false);
// v4.0.0: 移除"记住密码"（明文存 localStorage 有安全风险），只保留记住账号
const dbType = ref('local');  // 本地数据库 or 云数据库

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
};

onMounted(() => {
  const savedUsername = localStorage.getItem('rememberedUsername');
  if (savedUsername) {
    loginForm.username = savedUsername;
    rememberUsername.value = true;
  }
});

const handleArrowRight = async () => {
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    loading.value = true;
    errorMessage.value = '';

    try {
      const response = await request.post('/login', {
        username: loginForm.username,
        password: loginForm.password,
        db_type: dbType.value
      });

      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('tokenType', response.data.token_type || 'bearer');
        localStorage.setItem('username', loginForm.username);
        localStorage.setItem('loginTime', Date.now().toString());
        window.dispatchEvent(new Event('user-login'));
        
        // 记住账号（v4.0.0: 不再明文记住密码，避免 localStorage 泄露）
        if (rememberUsername.value) {
          localStorage.setItem('rememberedUsername', loginForm.username);
        } else {
          localStorage.removeItem('rememberedUsername');
        }
        // 清理旧的明文密码缓存
        localStorage.removeItem('rememberedPassword');
        
        ElMessage.success('登录成功');
        // v4.0.0: 登录后回到跳转前的页面（路由守卫/401 拦截器携带的 redirect）
        const redirectPath = (route.query.redirect as string) || '/';
        router.push(redirectPath);
      }
    } catch (error: any) {
      console.error('登录失败:', error);
      errorMessage.value = error?.response?.data?.detail || '登录失败，请重试';
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(64, 158, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(168, 85, 247, 0.1) 0%, transparent 40%);
  animation: gradientMove 15s ease infinite;
}

@keyframes gradientMove {
  0%, 100% { transform: translateX(0) translateY(0); }
  50% { transform: translateX(10px) translateY(10px); }
}

.login-container {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  z-index: 10;
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.logo-icon {
  background: linear-gradient(135deg, #ec4899, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: logoPulse 2s ease-in-out infinite;
}

@keyframes logoPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.logo-text {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #ec4899, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.login-form {
  margin-bottom: 20px;
}

.db-type-selector {
  display: flex;
  gap: 12px;
}

.db-type-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s;
  white-space: nowrap;
}

.db-type-btn:hover {
  border-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.1);
}

.db-type-btn.active {
  border-color: #ec4899;
  background: rgba(236, 72, 153, 0.15);
  color: #ec4899;
  box-shadow: 0 0 12px rgba(236, 72, 153, 0.2);
}

.login-input {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
}

.login-input:focus {
  border-color: #ec4899;
  box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.2);
}

.login-input .input-icon {
  color: rgba(255, 255, 255, 0.5);
}

.login-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #ec4899, #a855f7);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(236, 72, 153, 0.4);
  background: linear-gradient(135deg, #db2777, #9333ea);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
}

.remember-row {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.remember-checkbox {
  --el-checkbox-checked-text-color: rgba(255, 255, 255, 0.9);
  --el-checkbox-text-color: rgba(255, 255, 255, 0.7);
  --el-checkbox-bg-color: rgba(255, 255, 255, 0.08);
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 14px;
  animation: shake 0.3s ease-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@media (max-width: 480px) {
  .login-container {
    margin: 20px;
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .logo-text {
    font-size: 28px;
  }
}
</style>