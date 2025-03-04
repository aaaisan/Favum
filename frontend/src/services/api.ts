import axios from 'axios'

// 配置API客户端
const apiClient = axios.create({
  baseURL: '/api/v1', // 改回相对路径，使用Vite的代理功能
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000, // 10秒超时
  withCredentials: false // 跨域请求不发送 cookies
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      // 设置Authorization请求头
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`[API Client] 发送请求: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => {
    console.error('[API Client] 请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Client] 收到响应: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('[API Client] 网络错误，请检查后端服务是否正在运行:', error.message)
    } else if (error.response) {
      console.error(`[API Client] 响应错误 (${error.response.status}):`, error.response.data, 'URL:', error.config.url)
    } else {
      console.error('[API Client] 请求失败:', error.message)
    }
    return Promise.reject(error)
  }
)

console.log('[API Client] 初始化完成, baseURL:', apiClient.defaults.baseURL)

export default apiClient