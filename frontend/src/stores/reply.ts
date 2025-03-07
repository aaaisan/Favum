import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { Reply, ReplyForm } from '../types/post'

interface ReplyState {
  replies: Reply[]
  isLoading: boolean
  error: string | null
}

export const useReplyStore = defineStore('reply', {
  state: (): ReplyState => ({
    replies: [],
    isLoading: false,
    error: null
  }),

  actions: {
    async fetchReplies(postId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/posts/${postId}/replies`)
        this.replies = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取回复列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async createReply(replyData: ReplyForm) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.post('/replies', replyData)
        this.replies.push(response.data)
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '发送回复失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async updateReply(replyId: number, content: string) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.put(`/replies/${replyId}`, { content })
        const index = this.replies.findIndex(reply => reply.id === replyId)
        if (index !== -1) {
          this.replies[index] = response.data
        }
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '更新回复失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async deleteReply(replyId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        await apiClient.delete(`/replies/${replyId}`)
        this.replies = this.replies.filter(reply => reply.id !== replyId)
      } catch (err: any) {
        this.error = err.response?.data?.detail || '删除回复失败'
        throw err
      } finally {
        this.isLoading = false
      }
    }
  }
}) 