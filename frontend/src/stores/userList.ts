import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { User } from '../types/user'

interface UserListState {
  users: User[];
  totalUsers: number;
  isLoading: boolean;
  error: string | null;
}

export const useUserListStore = defineStore('userList', {
  state: (): UserListState => ({
    users: [],
    totalUsers: 0,
    isLoading: false,
    error: null
  }),

  actions: {
    async fetchUsers(page: number, limit: number, query?: string) {
      this.isLoading = true
      this.error = null
      
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString()
        })
        
        if (query) {
          params.append('query', query)
        }
        
        const response = await apiClient.get(`/users?${params}`)
        this.users = response.data.users
        this.totalUsers = response.data.total
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async deleteUser(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        await apiClient.delete(`/users/${userId}`)
        // 更新本地状态
        const userIndex = this.users.findIndex(user => user.id === userId)
        if (userIndex !== -1) {
          this.users[userIndex].is_deleted = true
        }
      } catch (err: any) {
        this.error = err.response?.data?.detail || '删除用户失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async restoreUser(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        await apiClient.post(`/users/${userId}/restore`)
        // 更新本地状态
        const userIndex = this.users.findIndex(user => user.id === userId)
        if (userIndex !== -1) {
          this.users[userIndex].is_deleted = false
        }
      } catch (err: any) {
        this.error = err.response?.data?.detail || '恢复用户失败'
        throw err
      } finally {
        this.isLoading = false
      }
    }
  }
}) 