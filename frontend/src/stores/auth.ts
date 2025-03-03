import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { User, LoginResponse } from '../types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem('token'),
    isLoading: false,
    error: null as string | null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    isAdmin: (state) => state.user?.role === 'admin' || state.user?.role === 'super_admin'
  },
  
  actions: {
    async register(username: string, email: string, password: string) {
      this.isLoading = true
      try {
        const response = await apiClient.post('/users', {
          username, email, password
        })
        return response.data
      } finally {
        this.isLoading = false
      }
    },
    
    async login(email: string, password: string) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.post<LoginResponse>('/auth/login', {
          email,
          password
        })
        
        const { access_token, user } = response.data
        this.token = access_token
        this.user = user
        
        localStorage.setItem('token', access_token)
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '登录失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    },
    
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    }
  }
})