import { defineStore } from 'pinia'
import apiClient from '../services/api'

interface User {
  id: number
  username: string
  email: string
  role: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
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
    
    async login(username: string, password: string, captcha_id: string, captcha_code: string) {
      this.isLoading = true
      try {
        const response = await apiClient.post('/auth/login', {
          username,
          password,
          captcha_id,
          captcha_code
        })
        
        const { access_token, user } = response.data
        this.setToken(access_token)
        this.user = user
        return response.data
      } finally {
        this.isLoading = false
      }
    },
    
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    },
    
    setToken(token: string) {
      this.token = token
      localStorage.setItem('token', token)
    }
  }
})