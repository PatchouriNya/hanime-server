import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus';

// 错误消息节流：同一消息在 interval 毫秒内只显示一次
let lastErrorMessage = '';
let lastErrorTime = 0;
const ERROR_MESSAGE_INTERVAL = 3000; // 3秒节流

let isRedirecting = false; // 防止 401 重复跳转

const showErrorMessage = (message: string) => {
    const now = Date.now();
    if (message === lastErrorMessage && now - lastErrorTime < ERROR_MESSAGE_INTERVAL) {
        return; // 节流：相同消息在间隔内不重复显示
    }
    lastErrorMessage = message;
    lastErrorTime = now;
    ElMessage.error(message);
};

const instance: AxiosInstance = axios.create({
    baseURL:'/api',
    timeout: 30000, // 30秒超时，避免请求积压
});

instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig =>{
        const token = localStorage.getItem('token');
        const tokenType = localStorage.getItem('tokenType') || 'bearer';

        if (token) {
            config.headers.Authorization = `${tokenType} ${token}`;
        }

        return config
    },
    (error: any): Promise<never> =>{
        showErrorMessage('请求发送失败');
        return Promise.reject(error)
    }
)

instance.interceptors.response.use(
    (response: AxiosResponse): AxiosResponse => response,
    (error: any): Promise<never> =>{
        // 超时错误单独处理
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            showErrorMessage('请求超时，请稍后再试');
            return Promise.reject(error);
        }

        // 网络错误（后端不可达）
        if (!error.response) {
            showErrorMessage('网络连接异常，请检查网络');
            return Promise.reject(error);
        }

        const status = error.response.status;
        // 判断当前是否在登录页或正在跳转登录页
        const isOnLoginPage = window.location.pathname === '/login';

        switch (status) {
            case 400:
                showErrorMessage('请求错误');
                break;
            case 401:
                localStorage.removeItem('token');
                localStorage.removeItem('tokenType');
                localStorage.removeItem('username');
                localStorage.removeItem('loginTime');
                if (!isRedirecting && !isOnLoginPage) {
                    isRedirecting = true;
                    showErrorMessage('登录已过期，请重新登录');
                    window.location.href = '/login';
                }
                // 延迟重置 isRedirecting，避免多个并发 401 重复跳转
                setTimeout(() => { isRedirecting = false; }, 3000);
                break;
            case 403:
                // 未登录时在登录页不弹"拒绝访问"，避免用户体验不佳
                if (!isOnLoginPage) {
                    showErrorMessage('拒绝访问');
                }
                break;
            case 404:
                // 未登录时在登录页不弹 404 错误
                if (!isOnLoginPage) {
                    showErrorMessage(`请求的资源不存在: ${error.config?.url || ''}`);
                }
                break;
            case 503:
                // 服务暂时不可用 - 不弹错误提示，静默失败让组件自己处理重试
                // 这种情况通常是外部网站请求失败，不需要打扰用户
                break;
            case 500:
                showErrorMessage('服务器内部错误');
                break;
            default:
                showErrorMessage(`请求失败 (${status})`);
        }
        return Promise.reject(error)
    }
)


// 默认导出
export default instance
