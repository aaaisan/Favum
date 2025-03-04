import { ref, computed, ComputedRef, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { usePostStore } from '../stores/post'
import apiClient from '../services/api'
import type { VoteType } from '../types/post'

export function usePostDetail(postId: number | ComputedRef<number>) {
  console.log('usePostDetail初始化，接收到的postId:', typeof postId === 'number' ? postId : postId.value)
  console.log('usePostDetail初始化，传入参数类型:', typeof postId, '是否为ComputedRef:', typeof postId === 'object' && 'value' in postId)
  
  const router = useRouter()
  const store = usePostStore()
  
  const post = computed(() => store.currentPost)
  const userVote = computed(() => store.userVote)
  const isLoading = computed(() => store.isLoading)
  const errorMessage = computed(() => store.error)
  
  // 获取postId的实际值
  const getPostId = () => {
    let id = typeof postId === 'number' ? postId : postId.value
    // 确保ID是数字类型
    id = Number(id)
    console.log('getPostId返回:', id, '类型:', typeof id)
    return id
  }
  
  const fetchPost = async () => {
    const currentPostId = getPostId()
    console.log(`usePostDetail.fetchPost: 开始获取帖子，ID: ${currentPostId}, isLoading=${isLoading.value}`)
    
    if (!currentPostId || isNaN(currentPostId) || currentPostId <= 0) {
      console.error('无效的帖子ID:', currentPostId)
      store.error = '无效的帖子ID'
      return
    }

    try {
      // 显示API客户端配置
      console.log('API基础URL:', apiClient.defaults.baseURL)
      console.log('API请求头:', JSON.stringify(apiClient.defaults.headers))
      
      // 重置error状态
      store.error = null
      
      // 调用store.fetchPost前记录store的状态
      console.log('调用store.fetchPost前的状态：', {
        isLoading: store.isLoading,
        error: store.error,
        hasCurrentPost: !!store.currentPost
      })
      
      console.log(`调用store.fetchPost(${currentPostId})`)
      await store.fetchPost(currentPostId)
      
      // 检查并记录调用后的状态
      console.log('store.fetchPost调用后的状态：', {
        isLoading: store.isLoading,
        error: store.error,
        hasCurrentPost: !!store.currentPost,
        currentPost: store.currentPost ? store.currentPost.id : null
      })
      
      if (store.currentPost) {
        console.log('获取帖子成功:', store.currentPost.id, store.currentPost.title)
      } else {
        console.warn('store.fetchPost调用成功，但currentPost为null')
        
        // 如果没有错误但也没有数据，设置一个错误
        if (!store.error) {
          store.error = '获取帖子成功但数据为空'
        }
      }
    } catch (error: any) {
      console.error('获取帖子详情失败:', error)
      console.error('错误类型:', error.constructor.name)
      console.error('错误栈:', error.stack)
      
      // 设置更详细的错误信息
      if (error.response) {
        console.error('错误响应详情:', {
          status: error.response.status,
          statusText: error.response.statusText,
          url: error.response.config?.url,
          data: error.response.data
        })
        
        if (error.response.data?.error?.message) {
          store.error = error.response.data.error.message
        } else if (error.response.data?.detail) {
          store.error = error.response.data.detail
        } else {
          store.error = `服务器返回错误: ${error.response.status}`
        }
      } else if (error.request) {
        console.error('请求已发送但没有收到响应:', error.request)
        store.error = '未收到服务器响应，请检查网络连接'
      } else if (error.message) {
        console.error('错误消息:', error.message)
        store.error = error.message
      } else {
        console.error('未知错误类型')
        store.error = '获取帖子详情失败，请稍后重试'
      }
    }
  }
  
  // 设置一个watchEffect来监听postId的变化
  watchEffect(() => {
    const currentPostId = getPostId()
    console.log(`usePostDetail watchEffect: 检测到postId为 ${currentPostId}, 类型: ${typeof currentPostId}`)
    if (currentPostId > 0) {
      console.log(`usePostDetail watchEffect: postId有效，值为 ${currentPostId}，准备获取数据`)
      // 重置状态
      store.error = null
      // 获取数据
      fetchPost()
    } else {
      console.warn(`usePostDetail watchEffect: postId无效，值为 ${currentPostId}，不获取数据`)
    }
  })
  
  const handleVote = async (voteType: VoteType) => {
    if (!post.value) return
    
    try {
      const response = await store.votePost(post.value.id, voteType)
      if (response.success) {
        // 投票成功，状态已在 store 中更新
      }
    } catch (error: any) {
      // 如果是未登录错误，跳转到登录页
      if (error.response?.status === 401) {
        router.push('/login')
      }
    }
  }
  
  const addComment = async (content: string) => {
    if (!post.value) return false
    
    // 检查用户是否登录
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return false
    }
    
    try {
      const response = await apiClient.post(`/posts/${post.value.id}/comments`, {
        content
      })
      
      // 如果评论添加成功，更新帖子的评论列表
      if (response.data && post.value) {
        if (!post.value.comments) {
          post.value.comments = []
        }
        post.value.comments.push(response.data)
      }
      
      return true
    } catch (error: any) {
      console.error('添加评论失败:', error)
      
      // 如果是未登录错误，跳转到登录页
      if (error.response?.status === 401) {
        router.push('/login')
      }
      
      return false
    }
  }
  
  return {
    post,
    userVote,
    isLoading,
    errorMessage,
    fetchPost,
    handleVote,
    addComment
  }
} 