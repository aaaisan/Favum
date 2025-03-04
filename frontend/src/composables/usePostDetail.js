import { ref, reactive } from 'vue'

/**
 * 文章详情组合式函数
 * @param {number} postId 文章ID
 * @returns {Object} 文章详情相关的状态和方法
 */
export function usePostDetail(postId) {
  const post = ref(null)
  const userVote = ref(null) // 'upvote', 'downvote', 或 null
  const isLoading = ref(true)
  const errorMessage = ref('')
  const comments = ref([])

  /**
   * 获取文章详情
   */
  const fetchPost = async () => {
    isLoading.value = true
    errorMessage.value = ''
    
    try {
      // 调用后端API获取文章详情
      const response = await fetch(`/api/posts/${postId}`)
      
      if (!response.ok) {
        throw new Error('获取文章失败')
      }
      
      const data = await response.json()
      post.value = data
      
      // 获取评论数据
      await fetchComments()
      
      // 更新文章浏览量
      updateViewCount()
      
    } catch (error) {
      console.error('获取文章详情失败:', error)
      errorMessage.value = error.message || '获取文章失败，请稍后再试'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取文章评论
   */
  const fetchComments = async () => {
    try {
      const response = await fetch(`/api/posts/${postId}/comments`)
      
      if (!response.ok) {
        throw new Error('获取评论失败')
      }
      
      const data = await response.json()
      comments.value = data
      
      // 如果post对象已存在，将comments数组添加到post对象中
      if (post.value) {
        post.value.comments = data
      }
      
    } catch (error) {
      console.error('获取评论失败:', error)
      // 这里我们不设置错误消息，因为这不是关键功能
    }
  }

  /**
   * 更新文章浏览量
   */
  const updateViewCount = async () => {
    try {
      await fetch(`/api/posts/${postId}/view`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
    } catch (error) {
      console.error('更新浏览量失败:', error)
      // 这个错误不会影响用户体验，所以我们只在控制台记录
    }
  }

  /**
   * 处理文章投票
   * @param {string} voteType - 'upvote' 或 'downvote'
   */
  const handleVote = async (voteType) => {
    // 检查用户是否已登录
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录后再进行投票')
      return
    }

    // 如果用户已经投了同一个票，则取消投票
    if (userVote.value === voteType) {
      voteType = 'cancel'
    }

    try {
      const response = await fetch(`/api/posts/${postId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ voteType })
      })

      if (!response.ok) {
        throw new Error('投票失败')
      }

      const data = await response.json()
      
      // 更新投票状态和计数
      userVote.value = voteType === 'cancel' ? null : voteType
      post.value.vote_count = data.vote_count
      
    } catch (error) {
      console.error('投票失败:', error)
      alert('投票失败，请稍后再试')
    }
  }

  // 初始检查用户是否已对该文章投票
  const checkUserVote = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`/api/posts/${postId}/user-vote`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        userVote.value = data.voteType // 'upvote', 'downvote', 或 null
      }
    } catch (error) {
      console.error('获取用户投票状态失败:', error)
    }
  }

  // 发表评论
  const addComment = async (content) => {
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录后再发表评论')
      return false
    }

    try {
      const response = await fetch(`/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content })
      })

      if (!response.ok) {
        throw new Error('发表评论失败')
      }

      // 刷新评论列表
      await fetchComments()
      return true
    } catch (error) {
      console.error('发表评论失败:', error)
      alert('发表评论失败，请稍后再试')
      return false
    }
  }

  return {
    post,
    comments,
    userVote,
    isLoading,
    errorMessage,
    fetchPost,
    handleVote,
    addComment
  }
} 