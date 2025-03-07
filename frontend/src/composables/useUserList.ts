import { ref, computed } from 'vue'
import { useUserListStore } from '../stores/userList'
import type { User } from '../types/user'

/**
 * 用户列表组合式函数
 * 封装用户列表页面的状态和逻辑
 */
export function useUserList() {
  const store = useUserListStore()
  
  // 搜索和分页状态
  const searchQuery = ref('')
  const page = ref(1)
  const pageSize = ref(10)
  
  // 从store中获取数据的计算属性
  const users = computed(() => store.users)
  const totalUsers = computed(() => store.totalUsers)
  const isLoading = computed(() => store.isLoading)
  const errorMessage = computed(() => store.error)
  
  /**
   * 搜索处理
   */
  const handleSearch = async () => {
    page.value = 1 // 重置页码
    await fetchUsers()
  }
  
  /**
   * 更改页码
   */
  const changePage = async (newPage: number) => {
    page.value = newPage
    await fetchUsers()
  }
  
  /**
   * 获取用户列表
   */
  const fetchUsers = async () => {
    try {
      await store.fetchUsers(page.value, pageSize.value, searchQuery.value)
    } catch (error) {
      console.error('获取用户列表失败:', error)
    }
  }
  
  /**
   * 删除用户
   */
  const deleteUser = async (userId: number) => {
    try {
      await store.deleteUser(userId)
    } catch (error) {
      console.error('删除用户失败:', error)
    }
  }
  
  /**
   * 恢复用户
   */
  const restoreUser = async (userId: number) => {
    try {
      await store.restoreUser(userId)
    } catch (error) {
      console.error('恢复用户失败:', error)
    }
  }
  
  return {
    // 状态
    searchQuery,
    page,
    pageSize,
    users,
    totalUsers,
    isLoading,
    errorMessage,
    
    // 方法
    handleSearch,
    changePage,
    fetchUsers,
    deleteUser,
    restoreUser
  }
} 