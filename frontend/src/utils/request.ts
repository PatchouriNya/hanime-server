import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus';

const instance: AxiosInstance = axios.create({
    baseURL:'/api',
})

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
        ElMessage.error('请求发送失败');
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
        if (error.response) {
            switch (error.response.status) {
                case 400:
                    ElMessage.error('请求错误');
                    break;
                case 401:
                    ElMessage.error('登录已过期，请重新登录');
                    localStorage.removeItem('token');
                    localStorage.removeItem('tokenType');
                    localStorage.removeItem('username');
                    localStorage.removeItem('loginTime');
                    window.location.href = '/login';
                    break;
                case 403:
                    ElMessage.error('拒绝访问');
                    break;
                case 404:
                    ElMessage.error('请求地址出错');
                    break;
                case 500:
                    ElMessage.error('服务器内部错误');
                    break;
                default:
                    ElMessage.error(`连接错误 ${error.response.status}`);
            }
        } else {
            ElMessage.error('网络连接异常，请稍后再试');
        }
        return Promise.reject(error)
    }
)


// 默认导出
export default instance