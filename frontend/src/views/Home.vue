<template>
  <div class="home-page">
    
    <div class="header-section">
      <div class="container">
        <h1 class="main-title">欢迎来到我们的社区论坛</h1>
        <p class="main-subtitle">加入讨论，分享知识，连接同好</p>
        
        <div class="header-actions">
          <router-link to="/register" class="primary-btn" v-if="!isLoggedIn">
            立即注册
          </router-link>
          <router-link to="/posts/new" class="primary-btn" v-else>
            发布新帖子
          </router-link>
          <router-link to="/categories" class="secondary-btn">
            浏览分类
          </router-link>
        </div>
      </div>
    </div>
    
    <div class="container main-content">
      <div class="flex-container">
        <div class="posts-section">
          <div class="section-header">
            <h2>最新讨论</h2>
            <div class="view-options">
              <button class="view-btn active">最新</button>
              <button class="view-btn">热门</button>
              <button class="view-btn">推荐</button>
            </div>
          </div>
          
          <div class="post-list">
            <div v-if="isLoading" class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载中...</p>
            </div>
            
            <div v-else-if="posts.length === 0" class="empty-state">
              暂无帖子
            </div>
            
            <div v-else class="post-card" v-for="post in posts" :key="post.id">
              <div class="post-header">
                <div class="user-avatar">{{ getUserInitials(post.author) }}</div>
                <div class="post-meta">
                  <div class="post-author">{{ post.author }}</div>
                  <div class="post-date">{{ formatDate(post.createdAt) }}</div>
                </div>
                <div class="post-category">{{ post.category }}</div>
              </div>
              
          <router-link :to="`/posts/${post.id}`" class="post-title">
            {{ post.title }}
          </router-link>
              
              <div class="post-excerpt">
                {{ post.excerpt }}
              </div>
              
              <div class="post-footer">
                <div class="post-stats">
                  <div class="stat-item">
                    <i class="icon">👁️</i>
                    <span>{{ post.viewCount }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="icon">💬</i>
                    <span>{{ post.commentCount }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="icon">👍</i>
                    <span>{{ post.likeCount }}</span>
                  </div>
                </div>
                
                <div class="post-tags">
                  <span class="tag" v-for="tag in post.tags" :key="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
      
      <div class="pagination">
              <button class="pagination-btn" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
          上一页
        </button>
              
              <div class="page-numbers">
        <button 
                  v-for="page in displayedPages" 
                  :key="page" 
                  class="page-number" 
                  :class="{ active: page === currentPage }"
                  @click="changePage(page)"
                >
                  {{ page }}
                </button>
              </div>
              
              <button class="pagination-btn" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
          下一页
        </button>
            </div>
          </div>
        </div>
        
        <div class="sidebar">
          <div class="sidebar-section">
            <h3>热门分类</h3>
            <div class="categories-list">
              <router-link 
                v-for="category in popularCategories" 
                :key="category.id" 
                :to="`/categories/${category.id}`"
                class="category-item"
                :style="{ backgroundColor: category.color + '1A' }"
              >
                <span class="category-name">{{ category.name }}</span>
                <span class="category-count">{{ category.postCount }}</span>
              </router-link>
            </div>
          </div>
          
          <div class="sidebar-section">
            <h3>热门标签</h3>
            <div class="tags-cloud">
              <router-link 
                v-for="tag in popularTags" 
                :key="tag.id" 
                :to="`/tags/${tag.id}`"
                class="tag-link"
                :style="{ fontSize: tagSize(tag.count) }"
              >
                {{ tag.name }}
              </router-link>
            </div>
          </div>
          
          <div class="sidebar-section">
            <h3>活跃用户</h3>
            <div class="active-users">
              <div class="user-item" v-for="user in activeUsers" :key="user.id">
                <div class="user-avatar">{{ getUserInitials(user.name) }}</div>
                <div class="user-info">
                  <router-link :to="`/users/${user.id}`" class="user-name">
                    {{ user.name }}
                  </router-link>
                  <div class="user-posts-count">{{ user.postCount }} 篇帖子</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import apiClient from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

// 定义类型
interface Post {
  id: string | number;
  title: string;
  author: string;
  category: string;
  excerpt: string;
  createdAt: Date;
  viewCount: number;
  commentCount: number;
  likeCount: number;
  tags: string[];
}

interface Category {
  id: string | number;
  name: string;
  color: string;
  postCount: number;
}

interface Tag {
  id: string | number;
  name: string;
  count: number;
}

interface User {
  id: string | number;
  name: string;
  postCount: number;
}

const authStore = useAuthStore()
const router = useRouter()
const isLoggedIn = computed(() => authStore.isAuthenticated)
const isLoading = ref(true)
const currentPage = ref(1)
const totalPages = ref(5)
const postsPerPage = 10

// 数据
const posts = ref<Post[]>([])
const popularCategories = ref<Category[]>([])
const popularTags = ref<Tag[]>([])
const activeUsers = ref<User[]>([])

// 获取帖子列表
const fetchPosts = async () => {
  isLoading.value = true
  try {
    console.log(`[Home] 获取帖子列表 - 认证状态: ${isLoggedIn.value}, token: ${localStorage.getItem('token') ? '存在' : '不存在'}`)
    const response = await apiClient.get('/posts', {
      params: {
        skip: (currentPage.value - 1) * postsPerPage,
        limit: postsPerPage,
      }
    })
    posts.value = response.data.posts.map((post: any) => ({
      id: post.id,
      title: post.title,
      author: `用户ID: ${post.author_id}`,
      category: post.category?.name || '未分类',
      excerpt: post.content.substring(0, 150) + '...',
      createdAt: new Date(post.created_at),
      viewCount: 0,
      commentCount: post.comments?.length || 0,
      likeCount: post.vote_count || 0,
      tags: post.tags?.map((tag: any) => tag.name) || []
    }))
    totalPages.value = Math.ceil(response.data.total / postsPerPage)
  } catch (error: any) {
    console.error('获取帖子列表失败:', error)
    
    // 特殊处理401未授权错误
    if (error.response && error.response.status === 401) {
      console.error('[Home] 获取帖子失败 - 401未授权')
      if (isLoggedIn.value) {
        // 更新状态
        console.log('[Home] 清理无效的认证状态')
        authStore.$reset()
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
    
    // 清空数据
    posts.value = []
    totalPages.value = 1
  } finally {
    isLoading.value = false
  }
}

// 获取热门分类
const fetchCategories = async () => {
  try {
    const response = await apiClient.get('/categories')
    popularCategories.value = response.data.slice(0, 5).map((category: any) => ({
      id: category.id,
      name: category.name,
      color: getCategoryColor(category.id),
      postCount: category.post_count || 0
    }))
  } catch (error) {
    console.error('获取分类列表失败:', error)
    // 清空数据而不是使用模拟数据
    popularCategories.value = []
  }
}

// 获取热门标签
const fetchTags = async () => {
  try {
    const response = await apiClient.get('/tags')
    popularTags.value = response.data.slice(0, 10).map((tag: any) => ({
      id: tag.id,
      name: tag.name,
      count: tag.post_count || 0
    }))
  } catch (error) {
    console.error('获取标签列表失败:', error)
    // 清空数据而不是使用模拟数据
    popularTags.value = []
  }
}

// 获取活跃用户
const fetchActiveUsers = async () => {
  // 检查是否有token（而不仅仅是isLoggedIn状态）
  const token = localStorage.getItem('token')
  if (!token) {
    console.log('[Home] 用户未登录，无法获取活跃用户数据')
    activeUsers.value = []
    return
  }
  
  // 检查用户角色
  const userData = localStorage.getItem('user')
  let userRole = 'user'
  
  if (userData) {
    try {
      const userObj = JSON.parse(userData)
      userRole = userObj.role || 'user'
      console.log('[Home] 用户角色:', userRole)
    } catch (e) {
      console.error('[Home] 解析用户数据失败:', e)
    }
  }
  
  // 只有管理员才能获取用户列表
  const isAdmin = userRole === 'admin' || userRole === 'super_admin' || userRole === 'moderator'
  
  if (!isAdmin) {
    console.log('[Home] 非管理员用户，使用模拟活跃用户数据')
    activeUsers.value = [
      {
        id: 1,
        name: '热心用户',
        postCount: 24
      },
      {
        id: 2,
        name: '新人分享',
        postCount: 16
      },
      {
        id: 3,
        name: '技术达人',
        postCount: 14
      },
      {
        id: 4,
        name: '资深用户',
        postCount: 11
      },
      {
        id: 5,
        name: '问题终结者',
        postCount: 8
      }
    ]
    return
  }
  
  try {
    console.log('[Home] 尝试获取活跃用户数据...')
    // 已登录则请求API
    const response = await apiClient.get('/users', {
      params: {
        sort: 'post_count',
        order: 'desc',
        limit: 5
      }
    })
    
    if (response.data && Array.isArray(response.data)) {
      activeUsers.value = response.data.map(user => ({
        id: user.id,
        name: user.username,
        postsCount: user.posts_count || 0,
        commentsCount: user.comments_count || 0
      }))
      console.log('[Home] 成功获取活跃用户数据:', activeUsers.value.length)
    } else {
      console.warn('[Home] 活跃用户数据格式不正确:', response.data)
      activeUsers.value = []
    }
  } catch (error: any) {
    console.error('[Home] 获取活跃用户数据失败:', error)
    
    // 特殊处理401未授权错误
    if (error.response && error.response.status === 401) {
      console.log('[Home] Token无效或已过期，清除本地登录状态')
      // 清除无效的token
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 重置状态
      activeUsers.value = []
    } else if (error.response && error.response.status === 403) {
      console.log('[Home] 权限不足，使用模拟活跃用户数据')
      activeUsers.value = [
        {
          id: 1,
          name: '热心用户',
          postCount: 24
        },
        {
          id: 2,
          name: '新人分享',
          postCount: 16
        },
        {
          id: 3,
          name: '技术达人',
          postCount: 14
        },
        {
          id: 4,
          name: '资深用户',
          postCount: 11
        },
        {
          id: 5,
          name: '问题终结者',
          postCount: 8
        }
      ]
    } else if (error.response && error.response.status === 500) {
      console.error('[Home] 服务器错误，使用模拟活跃用户数据')
      activeUsers.value = [
        {
          id: 1,
          name: '热心用户',
          postCount: 24
        },
        {
          id: 2,
          name: '新人分享',
          postCount: 16
        },
        {
          id: 3,
          name: '技术达人',
          postCount: 14
        },
        {
          id: 4,
          name: '资深用户',
          postCount: 11
        },
        {
          id: 5,
          name: '问题终结者',
          postCount: 8
        }
      ]
    } else {
      // 其他错误
      activeUsers.value = []
    }
  }
}

// 为分类分配固定颜色
const getCategoryColor = (categoryId: string | number): string => {
  const colors = [
    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#d35400', '#34495e', '#c0392b', '#16a085'
  ]
  return colors[Number(categoryId) % colors.length]
}

// 计算要显示的页码
const displayedPages = computed(() => {
  const pages = []
  const maxPages = 5 // 最多显示5个页码
  
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2))
  let end = Math.min(totalPages.value, start + maxPages - 1)
  
  if (end - start + 1 < maxPages && start > 1) {
    start = Math.max(1, end - maxPages + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// 根据标签的文章数量计算字体大小
const tagSize = (count: number): string => {
  if (popularTags.value.length === 0) return '1rem'
  
  const min = Math.min(...popularTags.value.map(t => t.count))
  const max = Math.max(...popularTags.value.map(t => t.count))
  const range = max - min
  
  if (range === 0) return '1rem'
  
  const size = 0.8 + ((count - min) / range) * 0.7
  return `${size}rem`
}

// 从用户名获取头像初始字母
const getUserInitials = (name: string): string => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

// 格式化日期
const formatDate = (date: Date): string => {
  if (!date) return ''
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚'
  }
  
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 1000))}分钟前`
  }
  
  // 小于1天
  if (diff < 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 60 * 1000))}小时前`
  }
  
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))}天前`
  }
  
  // 格式化为年月日
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

// 切换页码
const changePage = (page: number): void => {
  currentPage.value = page
  fetchPosts()
  window.scrollTo(0, 0)
}

// 页面加载时获取数据
onMounted(() => {
  console.log('[Home] 组件挂载 - 检查认证状态')
  
  // 确保认证状态已经初始化
  if (localStorage.getItem('token') && !authStore.isAuthenticated) {
    console.log('[Home] 发现token存在但未初始化认证状态，重新初始化')
    authStore.init()
  }
  
  // 更新登录状态显示
  console.log('[Home] 当前认证状态:', isLoggedIn.value)
  
  fetchPosts()
  fetchCategories()
  fetchTags()
  fetchActiveUsers()
})

// 监听认证状态变化
watch(() => authStore.isAuthenticated, (newValue) => {
  console.log('[Home] 认证状态发生变化:', newValue)
  // 当登录状态变化时，刷新数据
  fetchPosts()
  fetchActiveUsers()
})

</script>

<style scoped>
.home-page {
  width: 100%;
  background-color: #f8fafc;
  min-height: 100vh;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.header-section {
  background-color: #1e293b;
  background-image: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: white;
  padding: 5rem 0 4rem;
  text-align: center;
  margin-bottom: 2.5rem;
}

.main-title {
  font-size: 3rem;
  font-weight: 800;
  margin: 0 0 1rem;
  letter-spacing: -0.025em;
  background: linear-gradient(45deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.main-subtitle {
  font-size: 1.25rem;
  font-weight: 400;
  color: #cbd5e1;
  margin-bottom: 2.5rem;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.primary-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  background-color: #3b82f6;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
}

.primary-btn:hover {
  background-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 6px 10px rgba(59, 130, 246, 0.3);
}

.primary-btn:active {
  transform: translateY(0);
}

.secondary-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  background-color: transparent;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.secondary-btn:active {
  transform: translateY(0);
}

.main-content {
  margin-bottom: 4rem;
}

.flex-container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 2.5rem;
  align-items: start;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.view-options {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  padding: 0.5rem 1rem;
  background-color: transparent;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn:hover {
  background-color: #f1f5f9;
  color: #334155;
}

.view-btn.active {
  background-color: #e0f2fe;
  color: #0369a1;
  font-weight: 600;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  color: #64748b;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 4rem 0;
  color: #64748b;
  font-style: italic;
}

.post-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
  border-color: #cbd5e1;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.post-meta {
  flex: 1;
}

.post-author {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.post-date {
  font-size: 0.825rem;
  color: #64748b;
}

.post-category {
  padding: 0.35rem 0.75rem;
  background-color: #f1f5f9;
  border-radius: 4px;
  font-size: 0.825rem;
  font-weight: 500;
  color: #475569;
}

.post-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  text-decoration: none;
  line-height: 1.3;
  display: block;
  transition: color 0.2s;
}

.post-title:hover {
  color: #3b82f6;
}

.post-excerpt {
  color: #475569;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.post-stats {
  display: flex;
  gap: 1.25rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: #64748b;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.tag {
  padding: 0.25rem 0.6rem;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #64748b;
}

.pagination {
  margin-top: 2.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
}

.pagination-btn {
  padding: 0.625rem 1.25rem;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.pagination-btn:disabled {
  background-color: #f8fafc;
  border-color: #e2e8f0;
  color: #cbd5e1;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 0.5rem;
}

.page-number {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.page-number:hover:not(.active) {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.page-number.active {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
  font-weight: 600;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  position: sticky;
  top: 2rem;
}

.sidebar-section {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.sidebar-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  color: #334155;
  text-decoration: none;
  font-weight: 500;
  transition: transform 0.2s;
}

.category-item:hover {
  transform: translateX(5px);
}

.category-count {
  font-size: 0.825rem;
  color: #64748b;
  font-weight: 400;
}

.tags-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tag-link {
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s;
}

.tag-link:hover {
  color: #3b82f6;
}

.active-users {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  flex: 1;
}

.user-name {
  color: #1e293b;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
  display: block;
  margin-bottom: 0.25rem;
}

.user-name:hover {
  color: #3b82f6;
}

.user-posts-count {
  font-size: 0.825rem;
  color: #64748b;
}

/* Responsive design */
@media (max-width: 1200px) {
  .main-title {
    font-size: 2.5rem;
  }
  
  .flex-container {
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 2rem;
  }
}

@media (max-width: 1024px) {
  .flex-container {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    position: static;
    margin-top: 2.5rem;
  }
}

@media (max-width: 768px) {
  .header-section {
    padding: 3.5rem 0 3rem;
  }
  
  .main-title {
    font-size: 2rem;
  }
  
  .main-subtitle {
    font-size: 1.1rem;
  }
  
  .post-card {
    padding: 1.25rem;
  }
  
  .post-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .post-tags {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .post-header {
    flex-wrap: wrap;
  }
  
  .post-category {
    margin-top: 0.5rem;
  }
}

.test-links {
  margin: 2rem 0;
  padding: 1.5rem;
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}

.test-links h3 {
  color: #0369a1;
  margin-top: 0;
}

.test-links ul {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.test-links a {
  color: #0284c7;
  text-decoration: none;
}

.test-links a:hover {
  text-decoration: underline;
}

.direct-test {
  margin: 2rem 0;
  padding: 1.5rem;
  background-color: #f7fee7;
  border: 1px dashed #a3e635;
  border-radius: 8px;
}

.direct-test h3 {
  color: #3f6212;
  margin-top: 0;
}

.input-group {
  display: flex;
  margin: 1rem 0;
  gap: 0.5rem;
}

.test-input {
  flex-grow: 1;
  padding: 0.5rem;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

.test-button {
  padding: 0.5rem 1rem;
  background-color: #65a30d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.test-button:hover {
  background-color: #4d7c0f;
}

.test-loading {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #f1f5f9;
  border-radius: 4px;
  text-align: center;
}

.test-error {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #fee2e2;
  border-radius: 4px;
  color: #b91c1c;
}

.test-result {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #f0fdf4;
  border-radius: 4px;
}

.test-result-header {
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #d1fae5;
}

.test-result-content {
  white-space: pre-line;
  font-size: 0.9rem;
}

.debug-buttons {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.debug-button {
  padding: 0.5rem 1rem;
  background-color: #e4e4e7;
  color: #27272a;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.debug-button:hover {
  background-color: #d4d4d8;
}
</style>