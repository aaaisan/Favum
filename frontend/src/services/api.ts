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
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest' // 确保所有请求都带有这个头
  },
  // 禁用自动重定向处理，我们将自己处理重定向
  maxRedirects: 0,
  // 默认发送凭证
  withCredentials: true
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log(`[API Client] 发送请求: ${config.method?.toUpperCase()} ${config.url}`)
    
    // 获取token并添加到请求头 - 每次请求都重新从localStorage获取，避免使用过期引用
    let token = null;
    
    try {
      // 获取token
      token = localStorage.getItem('token');
      console.log(`[API Client] 当前token状态: ${token ? '存在' : '不存在'}${token ? '，长度:' + token.length : ''}`);
    } catch (e) {
      console.error(`[API Client] localStorage访问错误:`, e);
    }
    
    if (token && config.headers) {
      // 设置Authorization头（现在只设置一次，避免重复）
      config.headers['Authorization'] = `Bearer ${token}`;
      console.log(`[API Client] 已添加Authorization头: Bearer ${token.substring(0, 15)}...`);
    } else if (!token) {
      console.warn(`[API Client] 没有token，请求将不包含Authorization头`);
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

// 添加响应拦截器专门处理重定向
apiClient.interceptors.response.use(
  async (response) => {
    // 处理响应数据
    console.log(`[API Client] 收到响应: ${response.status} ${response.config.url}`)
    
    // 如果是重定向响应，我们自己处理重定向，保留认证头
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.location;
      console.log(`[API Client] 收到重定向响应: ${response.status} -> ${location || '未指定目标'}`)
      
      if (location) {
        // 创建一个新的请求配置，保留原始请求的所有头和配置
        const redirectConfig = { ...response.config };
        
        // 检查认证头
        const hasAuthHeader = redirectConfig.headers && 
                            (redirectConfig.headers['Authorization'] || 
                             redirectConfig.headers['authorization']);
                             
        console.log(`[API Client] 重定向请求${hasAuthHeader ? '包含' : '不包含'}认证头`);
        
        // 如果没有认证头但有token，强制添加
        if (!hasAuthHeader) {
          const token = localStorage.getItem('token');
          if (token && redirectConfig.headers) {
            console.log(`[API Client] 重定向请求添加认证头`);
            redirectConfig.headers['Authorization'] = `Bearer ${token}`;
          }
        }
        
        // 设置新的URL
        if (location.startsWith('http')) {
          // 绝对URL
          redirectConfig.url = location;
        } else if (location.startsWith('/')) {
          // 相对于根的URL
          redirectConfig.url = location.replace(/^\/api\/v1/, ''); // 移除前缀避免重复
        } else {
          // 相对URL
          const originalUrl = redirectConfig.url || '';
          const base = originalUrl.split('/').slice(0, -1).join('/');
          redirectConfig.url = `${base}/${location}`;
        }
        
        console.log(`[API Client] 手动处理重定向到: ${redirectConfig.url}`);
        console.log(`[API Client] 重定向请求头:`, JSON.stringify(redirectConfig.headers));
        
        // 确保重定向请求不会再次被自动重定向处理
        redirectConfig.maxRedirects = 0;
        
        try {
          // 发起新请求，保留原有配置包括认证头
          const redirectResponse = await apiClient(redirectConfig);
          console.log(`[API Client] 重定向请求成功, 状态码: ${redirectResponse.status}`);
          return redirectResponse;
        } catch (error) {
          console.error(`[API Client] 重定向请求失败:`, error);
          throw error;
        }
      }
    }
    
    return response;
  },
  (error) => {
    // 处理响应错误
    if (error.response) {
      // 服务器返回了错误状态码
      console.error(`[API Client] 响应错误: ${error.response.status} ${error.config?.url}`)
      
      // 如果是重定向错误，尝试手动处理
      if (error.response.status >= 300 && error.response.status < 400) {
        const location = error.response.headers?.location;
        console.log(`[API Client] 重定向错误: ${error.response.status} -> ${location || '未指定目标'}`)
        
        // 如果有重定向地址，尝试手动重定向
        if (location) {
          console.log(`[API Client] 尝试处理重定向错误...`);
          
          // 创建一个Promise，延迟后发起新请求
          return new Promise(resolve => {
            setTimeout(() => {
              // 获取原始配置
              const redirectConfig = { ...error.config };
              
              // 强制添加认证头
              const token = localStorage.getItem('token');
              if (token && redirectConfig.headers) {
                redirectConfig.headers['Authorization'] = `Bearer ${token}`;
                console.log(`[API Client] 重定向错误处理 - 添加认证头`);
              }
              
              // 设置新URL
              if (location.startsWith('http')) {
                redirectConfig.url = location;
              } else if (location.startsWith('/')) {
                redirectConfig.url = location.replace(/^\/api\/v1/, '');
              }
              
              console.log(`[API Client] 重定向错误处理 - 发起新请求: ${redirectConfig.url}`);
              
              // 发起新请求
              resolve(apiClient(redirectConfig));
            }, 100);
          });
        }
      }
      
      // 如果是401错误，可能是token无效，清除token
      if (error.response.status === 401) {
        console.error(`[API Client] 认证失败: ${error.response.data?.detail || error.response.data?.error?.message || '未知错误'}`)
        
        try {
          localStorage.removeItem('token')
          console.log(`[API Client] 已清除token`)
        } catch (e) {
          console.error(`[API Client] 清除token失败: ${e}`)
        }
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error(`[API Client] 无响应错误: ${error.message}`)
    } else {
      // 请求配置出错
      console.error(`[API Client] 请求错误: ${error.message}`)
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