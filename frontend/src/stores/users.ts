import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { User, UserList } from '../types'

export const useUsersStore = defineStore('users', {
  state: () => ({
    userList: null as UserList | null,
    currentUser: null as User | null,
    isLoading: false,
    error: null as string | null
  }),
  
  getters: {
    totalPages: (state) => {
      if (!state.userList) return 0
      return Math.ceil(state.userList.total / state.userList.page_size)
    }
  },
  
  actions: {
    // 获取用户列表
    async fetchUsers(page = 1, pageSize = 10, query = '') {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get('/users', {
          params: {
            page,
            page_size: pageSize,
            query
          }
        })
        this.userList = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取单个用户详情
    async fetchUserById(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}`)
        this.currentUser = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户信息失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 更新用户信息
    async updateUser(userId: number, userData: Partial<User>) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.put(`/users/${userId}`, userData)
        this.currentUser = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '更新用户信息失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 删除用户
    async deleteUser(userId: number) {
      try {
        const response = await apiClient.delete(`/users/${userId}`)
        
        // 如果当前查看的用户被删除，更新其状态
        if (this.currentUser && this.currentUser.id === userId) {
          this.currentUser.is_deleted = true
        }
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '删除用户失败'
        throw err
      }
    },
    
    // 恢复用户
    async restoreUser(userId: number) {
      try {
        const response = await apiClient.post(`/users/${userId}/restore`)
        
        // 如果当前查看的用户被恢复，更新其状态
        if (this.currentUser && this.currentUser.id === userId) {
          this.currentUser.is_deleted = false
        }
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '恢复用户失败'
        throw err
      }
    }
  }
}) 