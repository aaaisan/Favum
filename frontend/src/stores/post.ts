import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { Post, VoteType, VoteResponse, ForumCategory, PostForm } from '../types/post'

interface PostState {
  currentPost: Post | null;
  userVote: VoteType | null;
  categories: ForumCategory[];
  isLoading: boolean;
  error: string | null;
}

export const usePostStore = defineStore('post', {
  state: (): PostState => ({
    currentPost: null,
    userVote: null,
    categories: [],
    isLoading: false,
    error: null
  }),

  actions: {
    async fetchCategories() {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get('/categories')
        this.categories = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取分类列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async createPost(postData: PostForm) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.post('/posts', postData)
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '创建帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async fetchPost(postId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/posts/${postId}`)
        this.currentPost = response.data
        await this.fetchUserVote(postId)
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async fetchUserVote(postId: number) {
      try {
        const response = await apiClient.get(`/posts/${postId}/vote`)
        this.userVote = response.data.vote_type
      } catch (err: any) {
        if (err.response?.status !== 401) {
          console.error('获取投票状态失败:', err)
        }
        this.userVote = null
      }
    },

    async votePost(postId: number, voteType: VoteType): Promise<VoteResponse> {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.post(`/posts/${postId}/vote`, { vote_type: voteType })
        if (this.currentPost) {
          this.currentPost.vote_count = response.data.vote_count
        }
        this.userVote = voteType
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '投票失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async updatePost(postId: number, postData: Partial<PostForm>) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.put(`/posts/${postId}`, postData)
        this.currentPost = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '更新帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    async deletePost(postId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        await apiClient.delete(`/posts/${postId}`)
        this.currentPost = null
      } catch (err: any) {
        this.error = err.response?.data?.detail || '删除帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    }
  }
}) 