import { defineStore } from 'pinia'
import apiClient from '../services/api'
import type { Post, PostList } from '../types'

export const usePostsStore = defineStore('posts', {
  state: () => ({
    postList: null as PostList | null,
    userPosts: null as PostList | null,
    favoritesList: null as PostList | null,
    currentPost: null as Post | null,
    isLoading: false,
    error: null as string | null
  }),
  
  getters: {
    totalPages: (state) => {
      if (!state.postList) return 0
      return Math.ceil(state.postList.total / state.postList.page_size)
    },
    userPostsPages: (state) => {
      if (!state.userPosts) return 0
      return Math.ceil(state.userPosts.total / state.userPosts.page_size)
    },
    favoritesPages: (state) => {
      if (!state.favoritesList) return 0
      return Math.ceil(state.favoritesList.total / state.favoritesList.page_size)
    }
  },
  
  actions: {
    // 获取帖子列表
    async fetchPosts(page = 1, pageSize = 10, categoryId?: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const skip = (page - 1) * pageSize
        const params: any = { skip, limit: pageSize }
        if (categoryId) params.category_id = categoryId
        
        const response = await apiClient.get('/posts', { params })
        this.postList = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取帖子列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取单个帖子
    async fetchPost(postId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/posts/${postId}`)
        this.currentPost = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取帖子详情失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取用户帖子列表
    async fetchUserPosts(userId: number, page = 1, pageSize = 10) {
      this.isLoading = true
      this.error = null
      
      try {
        const skip = (page - 1) * pageSize
        const response = await apiClient.get(`/users/${userId}/posts`, {
          params: { skip, limit: pageSize }
        })
        this.userPosts = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取用户帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取用户收藏列表
    async fetchUserFavorites(userId: number) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}/favorites`)
        this.favoritesList = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取收藏列表失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 帖子投票
    async votePost(postId: number, voteType: 'upvote' | 'downvote') {
      try {
        const response = await apiClient.post(`/posts/${postId}/vote`, {
          vote_type: voteType
        })
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '投票失败'
        throw err
      }
    },
    
    // 点赞帖子
    async likePost(postId: number, isLike: boolean) {
      try {
        const response = await apiClient.post(`/posts/${postId}/vote`, {
          is_like: isLike
        })
        
        // 更新当前帖子的点赞数
        if (this.currentPost && this.currentPost.id === postId) {
          this.currentPost.like_count = response.data.like_count
        }
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '操作失败'
        throw err
      }
    },
    
    // 收藏帖子
    async favoritePost(postId: number) {
      try {
        const response = await apiClient.post(`/posts/${postId}/favorite`)
        
        // 更新当前帖子的收藏状态
        if (this.currentPost && this.currentPost.id === postId) {
          this.currentPost.is_favorite = true
        }
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '收藏失败'
        throw err
      }
    },
    
    // 取消收藏帖子
    async unfavoritePost(postId: number) {
      try {
        await apiClient.delete(`/posts/${postId}/favorite`)
        // 从收藏列表中移除
        if (this.favoritesList) {
          this.favoritesList.posts = this.favoritesList.posts.filter(
            post => post.id !== postId
          )
        }
      } catch (err: any) {
        this.error = err.response?.data?.detail || '取消收藏失败'
        throw err
      }
    }
  }
}) 