import { ref, computed, watch } from 'vue'
import { useUsersStore } from '../stores/users'
import type { User } from '../types'

/**
 * 用户列表组合式函数
 * 封装用户列表页面的状态和逻辑
 */
export function useUserList() {
  const usersStore = useUsersStore()
  
  // 搜索和分页状态
  const searchQuery = ref('')
  const page = ref(1)
  const pageSize = 10
  
  // 从store中获取数据的计算属性
  const users = computed<User[]>(() => usersStore.userList?.users || [])
  const isLoading = computed(() => usersStore.isLoading)
  const errorMessage = computed(() => usersStore.error)
  const totalUsers = computed(() => usersStore.userList?.total || 0)
  
  /**
   * 搜索处理
   */
  const handleSearch = () => {
    page.value = 1 // 重置为第一页
    fetchUsers()
  }
  
  /**
   * 更改页码
   */
  const changePage = (newPage: number) => {
    page.value = newPage
    fetchUsers()
  }
  
  /**
   * 获取用户列表
   */
  const fetchUsers = () => {
    usersStore.fetchUsers(page.value, pageSize, searchQuery.value)
  }
  
  /**
   * 删除用户
   */
  const deleteUser = async (userId: number) => {
    if (!confirm('确定要删除此用户吗？')) {
      return
    }
    
    try {
      await usersStore.deleteUser(userId)
      // 重新获取用户列表
      fetchUsers()
    } catch (error) {
      console.error('删除用户失败', error)
      return Promise.reject(error)
    }
  }
  
  /**
   * 恢复用户
   */
  const restoreUser = async (userId: number) => {
    try {
      await usersStore.restoreUser(userId)
      // 重新获取用户列表
      fetchUsers()
    } catch (error) {
      console.error('恢复用户失败', error)
      return Promise.reject(error)
    }
  }
  
  // 监听页码和搜索条件变化
  watch([page, searchQuery], () => {
    fetchUsers()
  })
  
  return {
    // 状态
    searchQuery,
    page,
    pageSize,
    users,
    isLoading,
    errorMessage,
    totalUsers,
    
    // 方法
    handleSearch,
    changePage,
    fetchUsers,
    deleteUser,
    restoreUser
  }
} 