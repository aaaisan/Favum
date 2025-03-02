import { defineStore } from 'pinia'
import apiClient from '../services/api'
import { User, UserStats, UserUpdateRequest } from '../types'

export const useProfileStore = defineStore('profile', {
  state: () => ({
    profile: null as User | null,
    stats: null as UserStats | null,
    isLoading: false,
    isUpdating: false,
    error: null as string | null,
    updateSuccess: false
  }),
  
  getters: {
    isAdmin: (state) => {
      return state.profile?.role === 'admin' || state.profile?.role === 'super_admin'
    },
    displayName: (state) => {
      return state.profile?.username || '用户'
    }
  },
  
  actions: {
    // 获取用户个人资料
    async fetchProfile(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}`)
        this.profile = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户资料失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取用户统计数据
    async fetchUserStats(userId: number) {
      try {
        // 这里应该调用真实的API，但目前使用模拟数据
        // const response = await apiClient.get(`/users/${userId}/stats`)
        // this.stats = response.data
        
        // 模拟数据
        this.stats = {
          postCount: 15,
          commentCount: 42,
          favoriteCount: 7,
          likeCount: 128
        }
        
        return this.stats
      } catch (err: any) {
        console.error('获取用户统计失败', err)
        // 不抛出错误，因为这不是关键功能
        return null
      }
    },
    
    // 更新用户个人资料
    async updateProfile(userId: number, userData: UserUpdateRequest) {
      this.isUpdating = true
      this.error = null
      this.updateSuccess = false
      
      try {
        const response = await apiClient.put(`/users/${userId}`, userData)
        this.profile = response.data
        this.updateSuccess = true
        
        // 3秒后重置成功状态
        setTimeout(() => {
          this.updateSuccess = false
        }, 3000)
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '更新用户资料失败'
        throw err
      } finally {
        this.isUpdating = false
      }
    }
  }
}) 