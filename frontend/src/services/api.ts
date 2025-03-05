import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, AxiosInstance } from 'axios'

// 记录正在进行的请求
const pendingRequests = new Map()
// 记录失败的请求和失败次数
const failedRequests = new Map()
// 最大重试次数
const MAX_RETRY_COUNT = 3

// 定义API基础URL
export const API_BASE_URL = '/api/v1'

// 创建一个带有默认配置的axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL, // 使用相对路径，由Vite代理处理
  timeout: 15000, // 增加超时时间
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // 不跟随重定向
  maxRedirects: 0
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log(`[API Client] 发送请求: ${config.method?.toUpperCase()} ${config.url}`)
    
    // 获取token并添加到请求头 - 每次请求都重新从localStorage获取，避免使用过期引用
    let token = null;
    
    // 测试localStorage功能
    try {
      // 先测试localStorage是否正常工作
      localStorage.setItem('test-key', 'test-value');
      const testValue = localStorage.getItem('test-key');
      console.log(`[API Client] localStorage测试: ${testValue === 'test-value' ? '正常' : '异常'}`);
      localStorage.removeItem('test-key');
      
      // 现在尝试获取真正的token
      token = localStorage.getItem('token');
      console.log(`[API Client] 当前token状态: ${token ? '存在' : '不存在'}${token ? '，长度:' + token.length : ''}`);
    } catch (e) {
      console.error(`[API Client] localStorage访问错误:`, e);
    }
    
    if (token && config.headers) {
      // 设置Authorization头，使用小写以确保兼容性
      config.headers['authorization'] = `Bearer ${token}`;
      // 同时设置大写版本以增加兼容性
      config.headers['Authorization'] = `Bearer ${token}`;
      console.log(`[API Client] 已添加Authorization头: Bearer ${token.substring(0, 15)}...`);
      
      // 添加X-Requested-With头，帮助服务器识别这是一个AJAX请求
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
      
      // 确保携带凭证
      config.withCredentials = true;
      
      // 打印所有请求头以便调试
      console.log(`[API Client] 完整请求头:`, JSON.stringify(config.headers));
    } else if (!token) {
      console.warn(`[API Client] 没有token，请求将不包含Authorization头`);
      // 尝试重新获取一次
      try {
        const manualToken = localStorage.getItem('token');
        console.log(`[API Client] 第二次尝试获取token: ${manualToken ? '存在' : '不存在'}`);
      } catch (e) {
        console.error(`[API Client] 第二次获取token失败:`, e);
      }
      
      // 仍然添加X-Requested-With头以标识AJAX请求
      if (config.headers) {
        config.headers['X-Requested-With'] = 'XMLHttpRequest';
      }
    }
    
    // 确保Content-Type正确
    if (config.method?.toLowerCase() === 'post' || config.method?.toLowerCase() === 'put') {
      if (config.headers && !config.headers['Content-Type'] && !(config.data instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json'
        console.log(`[API Client] 已添加Content-Type头: application/json`)
      }
    }
    
    // 请求URL作为唯一标识
    const requestId = config.url || ''
    
    // 检查同一个请求是否正在进行中
    if (pendingRequests.has(requestId)) {
      console.log(`[API Client] 请求 ${requestId} 正在进行中，跳过重复请求`)
      // 取消重复的请求
      return Promise.reject(new axios.Cancel('重复的请求已被取消'))
    }
    
    // 检查该请求是否已经失败多次
    if (failedRequests.has(requestId)) {
      const failCount = failedRequests.get(requestId)
      if (failCount >= MAX_RETRY_COUNT) {
        console.warn(`[API Client] 请求 ${requestId} 已失败 ${failCount} 次，不再重试`)
        return Promise.reject(new axios.Cancel('请求失败次数过多，已停止重试'))
      }
    }
    
    // 标记请求为进行中
    pendingRequests.set(requestId, true)
    
    return config
  },
  (error) => {
    // 处理请求错误
    console.error(`[API Client] 请求拦截器错误:`, error);
    return Promise.reject(error);
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log(`[API Client] 响应成功 (${response.status}): ${response.config.method?.toUpperCase()} ${response.config.url}`)
    
    // 清除进行中的请求标记
    const requestId = response.config.url || ''
    pendingRequests.delete(requestId)
    
    // 成功响应也清除失败计数
    failedRequests.delete(requestId)
    
    return response
  },
  (error: AxiosError) => {
    // 对响应错误做点什么
    if (error.response) {
      console.error(`[API Client] 响应错误 (${error.response.status}):`, error.response.data)
      
      // 如果是401错误（未授权），可能是token过期或无效
      if (error.response.status === 401) {
        console.warn('[API Client] 收到401未授权响应')
        
        // 获取当前路径
        const currentPath = window.location.pathname
        const isLoginPage = currentPath === '/login'
        
        // 清除本地存储的身份验证数据
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        console.log('[API Client] 已清除本地存储的身份验证数据')
        
        // 仅在非登录页发生401错误时重定向到登录页
        if (!isLoginPage) {
          console.log('[API Client] 未授权，保存当前路径并重定向到登录页')
          // 保存当前路径
          sessionStorage.setItem('returnPath', currentPath)
          
          // 重定向到登录页面
          window.location.href = '/login'
        } else {
          console.log('[API Client] 在登录页收到401错误，不需要重定向')
        }
      }
    } else if (error.request) {
      // 请求已经发出，但没有收到响应
      console.error('[API Client] 请求未收到响应:', error.request)
    } else {
      // 在设置请求时触发的错误
      console.error('[API Client] 请求配置错误:', error.message)
    }
    
    // 获取请求ID
    const requestId = error.config?.url || ''
    
    // 清除进行中的请求标记
    pendingRequests.delete(requestId)
    
    // 处理请求失败计数
    if (error.response && (error.response.status === 404 || error.response.status === 401)) {
      const currentCount = failedRequests.get(requestId) || 0
      failedRequests.set(requestId, currentCount + 1)
      
      if (currentCount + 1 >= MAX_RETRY_COUNT) {
        console.warn(`[API Client] 请求 ${requestId} 已达到最大失败次数 (${MAX_RETRY_COUNT})，不再重试`)
      }
    }
    
    if (error.code === 'ERR_NETWORK') {
      console.error('[API Client] 网络错误，请检查后端服务是否正在运行:', error.message)
    } else if (error.message === '重复的请求已被取消' || error.message === '请求失败次数过多，已停止重试') {
      // 这是我们自己取消的请求，不需要记录错误
      console.log('[API Client]', error.message)
    } else {
      console.error('[API Client] 请求失败:', error.message)
    }
    return Promise.reject(error)
  }
)

console.log('[API Client] 初始化完成, baseURL:', apiClient.defaults.baseURL)

// 导出apiClient实例，用于大多数请求
export default apiClient

// 导出通用API服务对象，包含常用的API方法
export const apiService = {
  // 用于登录的专用方法
  login: async (loginData: any) => {
    try {
      console.log('[API Service] 开始登录请求');
      return await apiClient.post('/auth/login', loginData);
    } catch (error) {
      console.error('[API Service] 登录请求失败:', error);
      throw error;
    }
  },
  
  // 获取验证码
  getCaptcha: async () => {
    try {
      console.log('[API Service] 获取验证码');
      // 添加时间戳防止缓存
      const timestamp = new Date().getTime();
      return await apiClient.get(`/captcha/generate?t=${timestamp}`, {
        responseType: 'blob',
        headers: {
          'Accept': 'image/png',
          'Cache-Control': 'no-cache'
        }
      });
    } catch (error) {
      console.error('[API Service] 获取验证码失败:', error);
      throw error;
    }
  },
  
  // 验证验证码
  verifyCaptcha: async (captchaId: string, captchaCode: string) => {
    try {
      return await apiClient.post(`/captcha/verify/${captchaId}`, { code: captchaCode });
    } catch (error) {
      console.error('[API Service] 验证码验证失败:', error);
      throw error;
    }
  },
  
  // 通用的GET请求方法
  get: async (url: string, config?: AxiosRequestConfig) => {
    try {
      return await apiClient.get(url, config);
    } catch (error) {
      console.error(`[API Service] GET ${url} 失败:`, error);
      throw error;
    }
  },
  
  // 通用的POST请求方法
  post: async (url: string, data?: any, config?: AxiosRequestConfig) => {
    try {
      return await apiClient.post(url, data, config);
    } catch (error) {
      console.error(`[API Service] POST ${url} 失败:`, error);
      throw error;
    }
  },
  
  // 通用的PUT请求方法
  put: async (url: string, data?: any, config?: AxiosRequestConfig) => {
    try {
      return await apiClient.put(url, data, config);
    } catch (error) {
      console.error(`[API Service] PUT ${url} 失败:`, error);
      throw error;
    }
  },
  
  // 通用的DELETE请求方法
  delete: async (url: string, config?: AxiosRequestConfig) => {
    try {
      return await apiClient.delete(url, config);
    } catch (error) {
      console.error(`[API Service] DELETE ${url} 失败:`, error);
      throw error;
    }
  }
};

// 用于直接axios请求的函数（应该尽量避免使用，推荐使用上面的apiClient或apiService）
export const directRequest = async (config: AxiosRequestConfig) => {
  try {
    console.log('[API Direct] 开始直接请求:', {
      method: config.method,
      url: config.url,
      // 如果数据中包含密码，不要记录
      data: config.data ? '数据已省略' : undefined
    });
    
    // 确保URL前缀正确
    if (config.url && !config.url.startsWith('http') && !config.url.startsWith('/api/v1')) {
      config.url = `/api/v1${config.url.startsWith('/') ? '' : '/'}${config.url}`;
    }
    
    return await axios(config);
  } catch (error) {
    console.error('[API Direct] 直接请求失败:', error);
    throw error;
  }
};