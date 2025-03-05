import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { LoginForm, RegisterForm, LoginResponse } from '../types/auth'
import type { User } from '../types/user'

export const useAuthStore = defineStore('auth', {
  state: () => {
    // 从localStorage中获取用户信息
    let user = null;
    let token = localStorage.getItem('token');
    
    console.log('[Auth Store 初始化] 从localStorage获取token:', token ? '存在' : '不存在');
    if (token) {
      console.log('[Auth Store 初始化] token长度:', token.length);
      console.log('[Auth Store 初始化] token前20个字符:', token.substring(0, 20));
    }
    
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        user = JSON.parse(userData);
        console.log('[Auth Store 初始化] 从localStorage获取用户信息:', user);
      } else {
        console.log('[Auth Store 初始化] localStorage中没有用户信息');
        
        // 尝试从token解析用户信息
        if (token) {
          try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
              return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            const payload = JSON.parse(jsonPayload);
            console.log('[Auth Store 初始化] 从token解析的payload:', payload);
            
            if (payload && payload.sub) {
              user = {
                id: Number(payload.sub),
                username: payload.username || payload.sub,
                email: payload.email || `user_${payload.sub}@example.com`,
                role: payload.role || 'user',
                bio: null,
                avatar_url: null,
                created_at: new Date().toISOString(),
                is_active: true,
                is_deleted: false
              };
              
              // 保存到localStorage
              localStorage.setItem('user', JSON.stringify(user));
              console.log('[Auth Store 初始化] 从token恢复并保存用户信息:', user);
            }
          } catch (e) {
            console.error('[Auth Store 初始化] 解析token失败:', e);
          }
        }
      }
    } catch (e) {
      console.error('[Auth Store 初始化] 从localStorage解析用户信息失败:', e);
      localStorage.removeItem('user');
    }
    
    return {
      token: token,
      user: user as User | null,
      isLoading: false,
      error: null as string | null
    }
  },
  
  getters: {
    isAuthenticated: (state) => {
      const result = !!state.token;
      console.log('[Auth Store Getter] isAuthenticated:', result, '当前token:', state.token ? '存在' : '不存在');
      return result;
    },
    currentUser: (state) => {
      console.log('[Auth Store Getter] currentUser:', state.user);
      return state.user;
    }
  },
  
  actions: {
    // 初始化函数，在应用启动时调用
    init() {
      console.log('[Auth Store] 初始化认证状态')
      // 确保重新从localStorage加载token，而不是使用state中可能已经过期的引用
      this.token = localStorage.getItem('token')
      
      if (!this.token) {
        console.log('[Auth Store] 未找到token，用户未登录')
        this.user = null
        return
      }
      
      console.log('[Auth Store] 找到token，长度:', this.token.length)
      console.log('[Auth Store] token前20个字符:', this.token.substring(0, 20))
      
      // 先尝试从localStorage加载用户信息
      try {
        const userData = localStorage.getItem('user')
        if (userData) {
          this.user = JSON.parse(userData)
          console.log('[Auth Store] 从localStorage加载用户信息成功')
          return
        }
      } catch (e) {
        console.error('[Auth Store] 从localStorage加载用户信息失败:', e)
      }
      
      // 如果没有用户信息，尝试从token解析
      try {
        if (!this.token) {
          throw new Error('Token为空')
        }
        
        // 分割token并获取payload部分
        const parts = this.token.split('.')
        if (parts.length !== 3) {
          throw new Error('Token格式不正确，应为三段式JWT')
        }
        
        const base64Url = parts[1]
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        
        // 解码Base64
        let decodedPayload
        try {
          decodedPayload = atob(base64)
        } catch (e) {
          throw new Error('无法解码token payload')
        }
        
        // 转为UTF-8字符串
        const jsonPayload = decodeURIComponent(
          decodedPayload.split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
          }).join('')
        )
        
        // 解析JSON
        const payload = JSON.parse(jsonPayload)
        console.log('[Auth Store] 从JWT解析的payload:', payload)
        
        // 检查payload中的必要字段
        if (!payload.sub) {
          throw new Error('Token中缺少sub(用户ID)字段')
        }
        
        // 创建用户对象
        this.user = {
          id: Number(payload.sub),
          username: payload.username || `user_${payload.sub}`,
          email: payload.email || `user_${payload.sub}@example.com`,
          role: payload.role || 'user',
          bio: null,
          avatar_url: null,
          created_at: new Date().toISOString(),
          is_active: true,
          is_deleted: false
        }
        
        console.log('[Auth Store] 从token解析并创建的用户信息:', this.user)
        
        // 将用户信息保存到localStorage
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (e) {
        console.error('[Auth Store] 解析token失败:', e)
        // 如果无法解析token，说明token可能无效，清除它
        this.token = null
        this.user = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    },
    
    /**
     * 用户登录
     * @param username 用户名
     * @param password 密码
     * @param captchaId 验证码ID
     * @param captchaCode 验证码
     * @returns 
     */
    async login(username: string, password: string, captchaId: string, captchaCode: string) {
      try {
        console.log(`[Auth Store] 开始登录过程 - 用户名: ${username}, 验证码ID: ${captchaId}`)
        
        // 清理之前的任何状态
        this.resetState()
        console.log(`[Auth Store] 已重置状态`)
        
        // 构建API数据
        const apiData = {
          username,
          password,
          captcha_id: captchaId,
          captcha_code: captchaCode
        }
        
        // 记录发送到API的数据
        console.log(`[Auth Store] 发送登录请求: `, apiData)
        
        // 发送登录请求
        const response = await apiClient.post('/auth/login', apiData)
        
        console.log(`[Auth Store] 登录响应: `, response.data)
        
        // 如果响应中包含token
        if (response.data.access_token) {
          console.log(`[Auth Store] 登录成功，获取到token，长度: ${response.data.access_token.length}，前15字符: ${response.data.access_token.substring(0, 15)}...`)
          
          // 清理任何旧的token - 保险起见
          try {
            console.log(`[Auth Store] 尝试清除任何现有的token`)
            localStorage.removeItem('token')
          } catch (e) {
            console.error(`[Auth Store] 清除旧token时出错: `, e)
          }
          
          try {
            // 测试localStorage是否正常工作
            console.log(`[Auth Store] 测试localStorage是否正常工作`)
            localStorage.setItem('test-auth', 'working')
            const testAuth = localStorage.getItem('test-auth')
            console.log(`[Auth Store] localStorage测试: ${testAuth === 'working' ? '成功' : '失败'}`)
            localStorage.removeItem('test-auth')
            
            // 尝试将token保存到localStorage
            console.log(`[Auth Store] 正在保存token到localStorage...`)
            localStorage.setItem('token', response.data.access_token)
            console.log(`[Auth Store] Token保存到localStorage成功`)
            
            // 确认localStorage中token是否存在并匹配
            const storedToken = localStorage.getItem('token')
            if (storedToken && storedToken === response.data.access_token) {
              console.log(`[Auth Store] localStorage验证成功: token已正确存储，长度: ${storedToken.length}`)
              console.log(`[Auth Store] 存储的token前15字符: ${storedToken.substring(0, 15)}...`)
            } else {
              console.error(`[Auth Store] localStorage验证失败: token存储不匹配或缺失`)
              if (storedToken) {
                console.log(`[Auth Store] 存储的token长度: ${storedToken.length}，前15字符: ${storedToken.substring(0, 15)}...`)
              } else {
                console.log(`[Auth Store] 存储的token为null或空`)
              }
              console.log(`[Auth Store] 原始token长度: ${response.data.access_token.length}`)
              
              // 第二次尝试存储
              console.log(`[Auth Store] 第二次尝试存储token...`)
              localStorage.setItem('token', response.data.access_token)
              const secondTry = localStorage.getItem('token')
              console.log(`[Auth Store] 第二次尝试结果: ${secondTry ? '成功' : '失败'}`)
            }
          } catch (e) {
            console.error(`[Auth Store] 无法保存token到localStorage: `, e)
          }
          
          // 设置token到store
          console.log(`[Auth Store] 设置token到store`)
          this.token = response.data.access_token
          
          // 解析token中的用户信息
          console.log(`[Auth Store] 准备解析token中的用户信息`)
          // 从JWT令牌解析用户信息
          try {
            // 确保token非空
            if (this.token) {
              const base64Url = this.token.split('.')[1]
              const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
              const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
              }).join(''))
              
              const payload = JSON.parse(jsonPayload)
              console.log('[Auth Store] 从JWT解析的payload:', payload)
              
              if (payload && payload.sub) {
                this.user = {
                  id: Number(payload.id || payload.sub),
                  username: payload.sub,
                  email: payload.email || `${payload.sub}@example.com`,
                  role: payload.role || 'user',
                  bio: null,
                  avatar_url: null,
                  created_at: new Date().toISOString(),
                  is_active: true,
                  is_deleted: false
                }
                
                console.log('[Auth Store] 保存用户信息到localStorage:', this.user)
                localStorage.setItem('user', JSON.stringify(this.user))
                
                console.log('[Auth Store] 登录成功! 用户:', this.user.username, '角色:', this.user.role)
              } else {
                this.user = null
                console.warn('[Auth Store] JWT payload中没有包含sub字段:', payload)
              }
            }
          } catch (e) {
            console.error('[Auth Store] 解析JWT失败:', e)
            this.user = null
          }
        }
        
        this.isLoading = false
        return response.data
      } catch (error: any) {
        this.isLoading = false
        this.error = error.response?.data?.detail || error.message || '登录失败'
        throw error
      }
    },
    
    async register(registerData: RegisterForm) {
      this.isLoading = true
      this.error = null
      
      console.log('Auth store: 发送注册请求，验证码ID:', registerData.captcha_id)
      
      try {
        // 创建一个不包含confirmPassword的数据对象
        const apiData = {
          username: registerData.username,
          email: registerData.email,
          password: registerData.password,
          bio: registerData.bio,
          captcha_id: registerData.captcha_id,
          captcha_code: registerData.captcha_code
        }
        
        console.log('Auth store: 发送到API的数据:', JSON.stringify(apiData))
        
        const response = await apiClient.post('/auth/register', apiData)
        console.log('Auth store: 注册成功，响应:', response.data)
        return response.data
      } catch (err: any) {
        console.error('Auth store: 注册失败:', err)
        if (err.response) {
          console.error('Auth store: 响应状态:', err.response.status)
          console.error('Auth store: 响应数据:', err.response.data)
        }
        this.error = err.response?.data?.detail || '注册失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    },
    
    resetState() {
      this.token = null
      this.user = null
      this.isLoading = false
      this.error = null
    }
  }
})