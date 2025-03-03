import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePostStore } from '../stores/post'
import type { VoteType } from '../types/post'

export function usePostDetail(postId: number) {
  const router = useRouter()
  const store = usePostStore()
  
  const post = computed(() => store.currentPost)
  const userVote = computed(() => store.userVote)
  const isLoading = computed(() => store.isLoading)
  const errorMessage = computed(() => store.error)
  
  const fetchPost = async () => {
    try {
      await store.fetchPost(postId)
    } catch (error) {
      console.error('获取帖子详情失败:', error)
    }
  }
  
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
  
  return {
    post,
    userVote,
    isLoading,
    errorMessage,
    fetchPost,
    handleVote
  }
} 