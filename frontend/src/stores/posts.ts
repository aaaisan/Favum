import { defineStore } from 'pinia'
import apiClient from '../services/api'

interface Post {
  id: number
  title: string
  content: string
  author_id: number
  author_name: string
  created_at: string
  updated_at: string
  view_count: number
  like_count: number
  comment_count: number
  is_favorite?: boolean
}

interface PostList {
  posts: Post[]
  total: number
  page: number
  page_size: number
}

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
        const params: any = { page, page_size: pageSize }
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
    
    // 获取用户帖子
    async fetchUserPosts(userId: number, page = 1, pageSize = 10) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}/posts`, {
          params: { page, page_size: pageSize }
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
    
    // 获取用户收藏
    async fetchUserFavorites(userId: number, page = 1, pageSize = 10) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await apiClient.get(`/users/${userId}/favorites`, {
          params: { page, page_size: pageSize }
        })
        this.favoritesList = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '获取收藏帖子失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取单个帖子详情
    async fetchPostById(postId: number) {
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
        const response = await apiClient.delete(`/posts/${postId}/favorite`)
        
        // 更新当前帖子的收藏状态
        if (this.currentPost && this.currentPost.id === postId) {
          this.currentPost.is_favorite = false
        }
        
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || '取消收藏失败'
        throw err
      }
    }
  }
}) 