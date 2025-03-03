import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1', // 后端API的基础URL
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
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('网络错误，请检查后端服务是否正在运行')
    } else if (error.response) {
      console.error('响应错误:', error.response.data)
    } else {
      console.error('请求失败:', error.message)
    }
    return Promise.reject(error)
  }
)

export default apiClient