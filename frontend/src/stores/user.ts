import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { User, UserStats, UserUpdateRequest } from '../types/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null as User | null,
    userStats: null as UserStats | null,
    isLoading: false,
    error: null as string | null
  }),

  actions: {
    async fetchUserProfile(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}`)
        this.currentUser = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户资料失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async fetchUserStats(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}/stats`)
        this.userStats = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户统计信息失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async updateUserProfile(userId: number, data: UserUpdateRequest) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.put(`/users/${userId}`, data)
        this.currentUser = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '更新用户资料失败'
        throw err
      } finally {
        this.isLoading = false
      }
    }
  }
}) 