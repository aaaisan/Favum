import { ref, computed, ComputedRef, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { usePostStore } from '../stores/post'
import apiClient from '../services/api'
import type { VoteType } from '../types/post'

export function usePostDetail(postId: number | ComputedRef<number>) {
  console.log('usePostDetail初始化，接收到的postId:', typeof postId === 'number' ? postId : postId.value)
  console.log('usePostDetail初始化，传入参数类型:', typeof postId, 'postId instanceof ComputedRef:', typeof postId === 'object' && 'value' in postId)
  if (typeof postId === 'object') {
    console.log('postId是对象，值为:', postId.value, '类型:', typeof postId.value)
    if (typeof postId.value === 'object') {
      console.error('警告: postId.value也是一个对象，这可能导致URL中出现[object Object]')
      console.error('postId.value的内容:', JSON.stringify(postId.value))
    }
  }
  
  const router = useRouter()
  const store = usePostStore()
  
  const post = computed(() => store.currentPost)
  const userVote = computed(() => store.userVote)
  const isLoading = computed(() => store.isLoading)
  const errorMessage = computed(() => store.error)
  
  // 添加一个标记变量，记录当前正在请求的postId，避免重复请求
  const currentFetchingId = ref<number | null>(null)
  
  // 获取postId的实际值
  const getPostId = () => {
    let id: any = typeof postId === 'number' ? postId : postId.value
    
    // 检查id是否是对象，如果是则转成字符串后再转数字
    if (typeof id === 'object') {
      console.error('警告: id是一个对象，内容:', JSON.stringify(id))
      if (id && 'id' in id) {
        console.log('尝试从对象中提取id属性')
        id = id.id
      } else {
        console.error('id对象中没有id属性，使用字符串转换')
        id = String(id)
      }
    }
    
    // 确保ID是数字类型
    const numericId = Number(id)
    console.log('getPostId原始值:', id, '类型:', typeof id, '转换后:', numericId, '类型:', typeof numericId)
    
    if (isNaN(numericId)) {
      console.error('无法将id转换为数字:', id)
      return 0
    }
    
    return numericId
  }
  
  const fetchPost = async () => {
    const currentPostId = getPostId()
    console.log(`usePostDetail.fetchPost: 开始获取帖子，ID: ${currentPostId}, isLoading=${isLoading.value}`)
    
    if (!currentPostId || isNaN(currentPostId) || currentPostId <= 0) {
      console.error('无效的帖子ID:', currentPostId)
      store.error = '无效的帖子ID'
      return
    }
    
    // 防止重复请求同一个ID
    if (currentFetchingId.value === currentPostId) {
      console.log(`ID为${currentPostId}的请求正在进行中，跳过重复请求`)
      return
    }
    
    // 如果已经有当前帖子且ID相同，且不处于加载状态，则不需要重新请求
    if (store.currentPost && store.currentPost.id === currentPostId && !isLoading.value) {
      console.log(`已有ID为${currentPostId}的帖子数据，无需重新请求`)
      return
    }
    
    try {
      // 设置正在请求的ID
      currentFetchingId.value = currentPostId
      
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
    } finally {
      // 重置正在请求的ID
      currentFetchingId.value = null
    }
  }
  
  // 防止重复请求的标志
  const isInitialRequest = ref(true)
  
  // 设置一个watchEffect来监听postId的变化
  watchEffect(() => {
    const currentPostId = getPostId()
    console.log(`usePostDetail watchEffect: 检测到postId为 ${currentPostId}, 类型: ${typeof currentPostId}`)
    
    // 仅在初次加载或ID变化时获取数据
    if (currentPostId > 0) {
      if (isInitialRequest.value || !store.currentPost || store.currentPost.id !== currentPostId) {
        console.log(`usePostDetail watchEffect: postId有效，值为 ${currentPostId}，准备获取数据`)
        // 重置状态
        store.error = null
        // 获取数据
        fetchPost()
        // 标记初始请求已完成
        isInitialRequest.value = false
      } else {
        console.log(`usePostDetail watchEffect: 已有ID为${currentPostId}的数据，跳过请求`)
      }
    } else {
      console.warn(`usePostDetail watchEffect: postId无效，值为 ${currentPostId}，不获取数据`)
    }
  })
  
  const handleVote = async (voteType: VoteType) => {
    if (!post.value) return
    
    try {
      console.log(`尝试对帖子 ${post.value.id} 进行${voteType}投票`)
      const response = await store.votePost(post.value.id, voteType)
      if (response.success) {
        console.log('投票成功，新的投票数:', post.value.vote_count)
      }
    } catch (error: any) {
      console.error('投票失败:', error)
      
      // 如果是未登录错误，跳转到登录页
      if (error.response?.status === 401) {
        console.log('用户未登录，跳转到登录页')
        router.push('/login')
      } else {
        // 其他错误可以提示用户
        alert(`投票失败: ${error.message || '未知错误'}`)
      }
    }
  }
  
  const addComment = async (content: string) => {
    if (!post.value) {
      console.error('找不到帖子信息，无法添加评论')
      return false
    }
    
    console.log('尝试添加评论到帖子:', post.value.id, '内容长度:', content.length)
    
    // 检查用户是否登录
    const token = localStorage.getItem('token')
    if (!token) {
      console.log('用户未登录，将重定向到登录页')
      
      // 保存当前状态以便登录后返回
      try {
        sessionStorage.setItem('returnPath', router.currentRoute.value.fullPath)
        sessionStorage.setItem('pendingAction', 'comment')
        sessionStorage.setItem('pendingComment', content)
        console.log('已保存评论状态到会话存储')
      } catch (e) {
        console.error('保存评论状态失败:', e)
      }
      
      router.push('/login')
      return false
    }
    
    try {
      console.log(`准备提交评论到帖子ID=${post.value.id}`)
      
      // 注意：后端API期望author_id是从令牌中获取的，所以不需要在前端手动添加
      const commentData = {
        content: content,
        post_id: post.value.id
      }
      
      console.log('准备发送的评论数据:', commentData)
      
      // 调用后端API添加评论
      const response = await apiClient.post('/comments/', commentData)
      
      console.log('评论发送成功, 响应:', response.data)
      
      // 如果评论添加成功，更新帖子的评论列表
      if (response.data && post.value) {
        if (!post.value.comments) {
          post.value.comments = []
        }
        post.value.comments.push(response.data)
        console.log('评论成功添加到帖子中')
      }
      
      return true
    } catch (error: any) {
      console.error('添加评论失败:', error)
      
      if (error.response) {
        console.error('服务器响应:', error.response.status, error.response.data)
        
        // 如果是未登录错误，跳转到登录页
        if (error.response.status === 401) {
          console.log('未授权错误，重定向到登录页')
          router.push('/login')
          return false
        }
        
        // 显示更详细的错误信息
        if (error.response.data && error.response.data.detail) {
          console.error('错误详情:', error.response.data.detail)
        }
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