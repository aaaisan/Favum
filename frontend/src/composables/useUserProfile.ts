import { computed, ref, ComputedRef } from 'vue'
import { useProfileStore } from '../stores/profile'
import { useUserForm } from './useUserForm'
import type { User, UserStats } from '../types'

/**
 * 用户个人资料组合式函数
 * @param userId - 用户ID计算属性
 * @returns 个人资料状态和方法
 */
export function useUserProfile(userId: ComputedRef<number>) {
  const profileStore = useProfileStore()
  const activeTab = ref('info')
  
  // 从store获取数据的计算属性
  const user = computed<User>(() => profileStore.profile || {
    username: '',
    email: '',
    role: 'user'
  })
  
  const userStats = computed<UserStats>(() => profileStore.stats || {
    postCount: 0,
    commentCount: 0,
    favoriteCount: 0,
    likeCount: 0
  })
  
  const isLoading = computed(() => profileStore.isLoading)
  const errorMessage = computed(() => profileStore.error)
  const updateSuccess = computed(() => profileStore.updateSuccess)
  
  // 获取用户表单功能
  const {
    form,
    errors,
    isSubmitting,
    resetForm,
    validate,
    getUpdateData
  } = useUserForm()
  
  /**
   * 初始化编辑表单
   */
  const initEditForm = () => {
    form.username = user.value.username || ''
    form.email = user.value.email || ''
    form.bio = user.value.bio || ''
    form.password = ''
    form.confirmPassword = ''
  }
  
  /**
   * 取消编辑
   */
  const cancelEdit = () => {
    initEditForm()
    activeTab.value = 'info'
  }
  
  /**
   * 更新个人资料
   */
  const updateProfile = async () => {
    if (!validate({ isPasswordRequired: false })) {
      return
    }
    
    try {
      await profileStore.updateProfile(userId.value, getUpdateData())
    } catch (error: any) {
      console.error('更新用户资料失败', error)
      
      // 处理特定字段的错误
      if (error.response?.data?.detail === '用户名已被使用') {
        errors.username = '该用户名已被使用'
      } else if (error.response?.data?.detail === '邮箱已被注册') {
        errors.email = '该邮箱已被注册'
      }
    }
  }
  
  /**
   * 获取用户资料
   */
  const fetchUserProfile = async () => {
    try {
      await profileStore.fetchProfile(userId.value)
      initEditForm()
      
      // 获取用户统计信息
      await profileStore.fetchUserStats(userId.value)
    } catch (error) {
      console.error('获取用户资料失败', error)
    }
  }
  
  return {
    user,
    userStats,
    isLoading,
    errorMessage,
    isSubmitting,
    updateSuccess,
    activeTab,
    form,
    errors,
    fetchUserProfile,
    updateProfile,
    cancelEdit
  }
} 