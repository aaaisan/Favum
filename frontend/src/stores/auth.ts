import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { LoginForm, RegisterForm, LoginResponse } from '../types/auth'
import type { User } from '../types/user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null as User | null,
    isLoading: false,
    error: null as string | null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user
  },
  
  actions: {
    async login(loginData: LoginForm) {
      this.isLoading = true
      this.error = null
      
      console.log('Auth store: 发送登录请求，验证码ID:', loginData.captcha_id)
      console.log('Auth store: 发送登录请求，验证码内容:', loginData.captcha_code)
      console.log('Auth store: 完整的登录数据:', JSON.stringify(loginData))
      
      try {
        // 确保数据是一个普通对象，而不是响应式对象
        const apiData = {
          username: loginData.username,
          password: loginData.password,
          captcha_id: loginData.captcha_id,
          captcha_code: loginData.captcha_code
        }
        
        console.log('Auth store: 发送到API的数据:', JSON.stringify(apiData))
        
        const response = await apiClient.post<LoginResponse>('/auth/login', apiData, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        this.token = response.data.access_token
        this.user = response.data.user
        localStorage.setItem('token', response.data.access_token)
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '登录失败'
        throw err
      } finally {
        this.isLoading = false
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
    }
  }
})