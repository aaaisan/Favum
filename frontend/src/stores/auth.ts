import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isLoading: false
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token
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
    
    // 其他认证相关方法...
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    }
  }
})