import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus';

// 错误消息节流：同一消息在 interval 毫秒内只显示一次
let lastErrorMessage = '';
let lastErrorTime = 0;
const ERROR_MESSAGE_INTERVAL = 2000; // 2秒节流

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
    (response: AxiosResponse): AxiosResponse =>{
        if (response.data && response.data.success) {
            ElMessage.success(response.data.message || '操作成功');
        }
        return response
    },
    (error: any): Promise<never> =>{
        // 超时错误单独处理
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            showErrorMessage('请求超时，请稍后再试');
            return Promise.reject(error);
        }

        if (error.response) {
            switch (error.response.status) {
                case 400:
                    showErrorMessage('请求错误');
                    break;
                case 401:
                    showErrorMessage('登录已过期，请重新登录');
                    localStorage.removeItem('token');
                    localStorage.removeItem('tokenType');
                    localStorage.removeItem('username');
                    localStorage.removeItem('loginTime');
                    if (!isRedirecting) {
                        isRedirecting = true;
                        window.location.href = '/login';
                    }
                    break;
                case 403:
                    showErrorMessage('拒绝访问');
                    break;
                case 404:
                    showErrorMessage('请求地址出错');
                    break;
                case 500:
                    showErrorMessage('服务器内部错误');
                    break;
                default:
                    showErrorMessage(`连接错误 ${error.response.status}`);
            }
        } else {
            showErrorMessage('网络连接异常，请稍后再试');
        }
        return Promise.reject(error)
    }
)


// 默认导出
export default instance
