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
      console.log(`store.fetchPost: 开始获取帖子，ID: ${postId}, 类型: ${typeof postId}`)
      this.isLoading = true
      this.error = null
      console.log('已设置 isLoading =', this.isLoading)
      
      try {
        // 确保postId是数字
        const numericPostId = Number(postId)
        if (isNaN(numericPostId) || numericPostId <= 0) {
          throw new Error(`无效的帖子ID: ${postId}`)
        }
        
        console.log(`正在获取帖子ID: ${numericPostId}的详情，完整URL: /posts/${numericPostId}`)
        
        const url = `/posts/${numericPostId}`
        const fullUrl = `${apiClient.defaults.baseURL}${url}`
        console.log(`发送GET请求到完整URL: ${fullUrl}`)
        
        const startTime = Date.now()
        const response = await apiClient.get(url)
        const endTime = Date.now()
        console.log(`请求耗时: ${endTime - startTime}ms`)
        
        console.log('获取帖子详情响应状态:', response.status)
        console.log('响应头:', JSON.stringify(response.headers))
        
        if (response.data) {
          console.log('帖子数据:', JSON.stringify(response.data).substring(0, 200) + '...')
          this.currentPost = response.data
          await this.fetchUserVote(numericPostId)
          console.log('状态更新完成，currentPost已设置，准备返回数据')
          return response.data
        } else {
          console.error('响应中没有数据')
          this.error = '获取帖子数据失败，响应中没有数据'
          throw new Error('响应中没有数据')
        }
      } catch (err: any) {
        console.error('获取帖子详情失败:', err)
        console.error('错误名称:', err.name)
        console.error('错误消息:', err.message)
        
        // 打印完整错误对象以便调试
        try {
          console.error('完整错误对象:', JSON.stringify(err, Object.getOwnPropertyNames(err)))
        } catch (e) {
          console.error('无法序列化错误对象')
        }
        
        if (err.response) {
          console.error('错误响应状态:', err.response.status)
          console.error('错误响应状态文本:', err.response.statusText)
          console.error('错误URL:', err.response.config?.url)
          console.error('错误响应数据:', JSON.stringify(err.response.data))
          
          if (err.response.status === 404) {
            this.error = `帖子不存在 (ID: ${postId})`
          } else if (err.response.data?.error?.message) {
            this.error = err.response.data.error.message
          } else if (err.response.data?.detail) {
            this.error = err.response.data.detail
          } else {
            this.error = `服务器错误 (${err.response.status}): ${err.response.statusText}`
          }
        } else if (err.request) {
          console.error('请求已发送但没有收到响应')
          this.error = '未收到服务器响应，请检查网络连接和后端服务是否正在运行'
        } else if (err.message) {
          console.error('错误消息:', err.message)
          
          // 检查常见的网络错误
          if (err.message.includes('Network Error')) {
            this.error = '网络错误: 无法连接到后端服务，请确保后端服务正在运行'
          } else if (err.message.includes('timeout')) {
            this.error = '请求超时: 后端服务响应时间过长'
          } else if (err.code === 'ERR_NETWORK') {
            this.error = '网络错误: 请检查网络连接和后端服务'
          } else {
            this.error = `获取帖子失败: ${err.message}`
          }
        } else {
          this.error = '获取帖子失败，发生未知错误'
        }
        
        throw new Error(this.error || '获取帖子失败')
      } finally {
        console.log('store.fetchPost: finally块执行，设置 isLoading = false')
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