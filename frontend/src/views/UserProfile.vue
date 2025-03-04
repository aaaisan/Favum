<template>
  <div class="profile-page">
    <div class="container">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="errorMessage" class="error-state">
        <div class="error-icon">!</div>
        <h2>加载失败</h2>
        <p>{{ errorMessage }}</p>
        <router-link to="/" class="primary-btn">返回首页</router-link>
      </div>
      
      <template v-else-if="user">
        <div class="profile-header">
          <div class="profile-cover" :style="{ backgroundColor: getCoverColor() }"></div>
          
          <div class="profile-header-content">
            <div class="profile-avatar">
              <span v-if="!user.avatar">{{ getUserInitials(user.name) }}</span>
              <img v-else :src="user.avatar" :alt="user.name" />
            </div>
            
            <div class="profile-info">
              <div class="profile-meta">
                <h1 class="profile-name">{{ user.name }}</h1>
                <div class="profile-role" :class="getRoleClass(user.role)">
                  {{ getRoleText(user.role) }}
                </div>
              </div>
              
              <div class="profile-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ user.postCount }}</div>
                  <div class="stat-label">发帖数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ user.commentCount }}</div>
                  <div class="stat-label">评论数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ user.likeCount }}</div>
                  <div class="stat-label">获赞数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatDate(user.joinedAt, 'YYYY-MM-DD') }}</div>
                  <div class="stat-label">注册时间</div>
                </div>
              </div>
              
              <div class="profile-bio" v-if="user.bio">
                {{ user.bio }}
              </div>
              <div class="profile-bio empty" v-else>
                该用户暂未设置个人简介
              </div>
            </div>
            
            <div class="profile-actions" v-if="isCurrentUser">
              <button class="primary-btn" @click="editProfile">
                编辑个人资料
              </button>
            </div>
            
            <div class="profile-actions" v-else>
              <button 
                class="secondary-btn" 
                :class="{ active: isFollowing }"
                @click="toggleFollow"
              >
                {{ isFollowing ? '已关注' : '关注' }}
              </button>
              
              <button class="secondary-btn" @click="sendMessage">
                发送消息
              </button>
            </div>
          </div>
        </div>
        
        <div class="profile-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'posts' }"
            @click="activeTab = 'posts'"
          >
            发帖
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'comments' }"
            @click="activeTab = 'comments'"
          >
            评论
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'liked' }"
            @click="activeTab = 'liked'"
          >
            赞过的帖子
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'following' }"
            @click="activeTab = 'following'"
          >
            关注的人
          </button>
        </div>
        
        <!-- 发帖列表 -->
        <div v-if="activeTab === 'posts'" class="tab-content">
          <div class="posts-list">
            <div v-if="isTabLoading" class="loading-tab">
              <div class="loading-spinner small"></div>
              <p>加载中...</p>
            </div>
            
            <div v-else-if="posts.length === 0" class="empty-tab">
              <div class="empty-icon">📝</div>
              <p>暂无发帖记录</p>
            </div>
            
            <div v-else class="post-grid">
              <div class="post-card" v-for="post in posts" :key="post.id">
                <div class="post-header">
                  <div class="post-meta">
                    <div class="post-category">{{ getCategoryName(post.category_id) }}</div>
                    <div class="post-date">{{ formatDate(post.created_at) }}</div>
                  </div>
                </div>
                
                <router-link :to="`/posts/${post.id}`" class="post-title">
                  {{ post.title }}
                </router-link>
                
                <div class="post-excerpt">
                  {{ getExcerpt(post.content) }}
                </div>
                
                <div class="post-footer">
                  <div class="post-stats">
                    <div class="stat-item">
                      <i class="icon">👁️</i>
                      <span>{{ post.views || 0 }}</span>
                    </div>
                    <div class="stat-item">
                      <i class="icon">💬</i>
                      <span>{{ post.comments?.length || 0 }}</span>
                    </div>
                    <div class="stat-item">
                      <i class="icon">👍</i>
                      <span>{{ post.likes || 0 }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="pagination" v-if="posts.length > 0">
              <button 
                class="pagination-btn" 
                :disabled="currentPage === 1" 
                @click="changePage(currentPage - 1)"
              >
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
              
              <button 
                class="pagination-btn" 
                :disabled="currentPage === totalPages" 
                @click="changePage(currentPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
        
        <!-- 其他标签页内容 (评论/赞过的帖子/关注的人) -->
        <div v-else class="tab-content">
          <div class="coming-soon">
            <div class="coming-soon-icon">🚧</div>
            <h3>功能开发中</h3>
            <p>{{ getTabMessage() }}</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 加载状态
const isLoading = ref(true)
const isTabLoading = ref(true)
const errorMessage = ref('')

// 用户数据
const user = ref({
  id: 1,
  name: '张三',
  role: 'user', // user, moderator, admin, super_admin
  avatar: '',
  bio: '前端开发工程师，热爱技术分享，喜欢帮助他人解决问题。擅长 Vue.js, React, TypeScript。业余爱好包括阅读、烹饪和徒步旅行。',
  postCount: 42,
  commentCount: 156,
  likeCount: 238,
  joinedAt: new Date(Date.now() - 86400000 * 180) // 6个月前
})

// 标签页数据
const activeTab = ref('posts')
const currentPage = ref(1)
const totalPages = ref(5)
const posts = ref<any[]>([])

// 关系状态
const isCurrentUser = ref(true) // 是否为当前登录用户
const isFollowing = ref(false) // 是否已关注

// Add missing categories reference
const categories = ref<any[]>([])

// Add userId from route params
const userId = computed(() => route.params.id)

// 获取用户名缩写
const getUserInitials = (name: string) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

// 获取角色文本
const getRoleText = (role: string) => {
  switch (role) {
    case 'admin': return '管理员'
    case 'super_admin': return '超级管理员'
    case 'moderator': return '版主'
    default: return '会员'
  }
}

// 获取角色样式类
const getRoleClass = (role: string) => {
  switch (role) {
    case 'admin': return 'role-admin'
    case 'super_admin': return 'role-admin'
    case 'moderator': return 'role-moderator'
    default: return 'role-user'
  }
}

// 获取封面颜色
const getCoverColor = () => {
  const colors = [
    '#3498db', '#2ecc71', '#9b59b6', '#f1c40f', 
    '#e74c3c', '#1abc9c', '#34495e', '#e67e22'
  ]
  const hash = user.value.name.split('').reduce((acc, char) => {
    return acc + char.charCodeAt(0)
  }, 0)
  
  return colors[hash % colors.length]
}

// 获取标签页消息
const getTabMessage = () => {
  switch (activeTab.value) {
    case 'comments': return '评论列表功能即将上线，敬请期待'
    case 'liked': return '赞过的帖子功能即将上线，敬请期待'
    case 'following': return '关注列表功能即将上线，敬请期待'
    default: return '该功能正在开发中，敬请期待'
  }
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

// 格式化日期
const formatDate = (date: Date, format?: string) => {
  if (format === 'YYYY-MM-DD') {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }

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
  
  // 小于30天
  if (diff < 30 * 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))}天前`
  }
  
  // 其他情况显示完整日期
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 切换页面
const changePage = (page: number) => {
  currentPage.value = page
  loadTabData()
}

// 编辑个人资料
const editProfile = () => {
  router.push('/settings/profile')
}

// 切换关注状态
const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
  // 实际应用中这里会调用API
  console.log(isFollowing.value ? '关注用户' : '取消关注', user.value.id)
}

// 发送消息
const sendMessage = () => {
  // 实际应用中这里会跳转到消息页面或打开消息模态框
  console.log('发送消息给用户:', user.value.id)
  alert('消息功能即将上线')
}

// Fetch user posts with proper error handling
const fetchUserPosts = async () => {
  isTabLoading.value = true
  try {
    // Replace with your actual API endpoint
    const response = await fetch(`/api/users/${userId.value}/posts`)
    if (!response.ok) {
      throw new Error('Failed to fetch user posts')
    }
    posts.value = await response.json()
  } catch (error) {
    console.error('Error fetching user posts:', error)
  } finally {
    isTabLoading.value = false
  }
}

// Fetch categories for post display
const fetchCategories = async () => {
  try {
    const response = await fetch('/api/categories')
    if (response.ok) {
      categories.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching categories:', error)
  }
}

// Update the user data loading function
const fetchUserData = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`/api/users/${userId.value}`)
    if (!response.ok) {
      throw new Error('Failed to fetch user data')
    }
    user.value = await response.json()
    isCurrentUser.value = checkIfCurrentUser(user.value.id)
  } catch (error) {
    console.error('Error fetching user data:', error)
    errorMessage.value = 'Failed to load user data'
  } finally {
    isLoading.value = false
  }
}

// Helper to check if viewing the current logged-in user
const checkIfCurrentUser = (id: number) => {
  // In a real app, you would compare with the logged-in user ID from auth state
  // For now, we'll just return a placeholder
  return false
}

// Replace the onMounted function
onMounted(() => {
  fetchUserData()
  fetchCategories()
  loadTabData()
})

// Update the loadTabData function to use fetchUserPosts
const loadTabData = () => {
  if (activeTab.value === 'posts') {
    fetchUserPosts()
  } else {
    // Other tabs data fetching would go here
    isTabLoading.value = false
  }
}

// Get category name from category ID - fix the parameter type
const getCategoryName = (categoryId: number | null) => {
  if (!categoryId) return '未分类'
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : '未分类'
}

// Get excerpt from content
const getExcerpt = (content: string) => {
  if (!content) return ''
  // Strip HTML tags and get first 150 characters
  const plainText = content.replace(/<[^>]*>/g, '')
  return plainText.length > 150 ? plainText.substring(0, 150) + '...' : plainText
}
</script>

<style scoped>
.profile-page {
  width: 100%;
  background-color: #f8fafc;
  min-height: 100vh;
  padding-bottom: 4rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6rem 0;
  text-align: center;
  min-height: 40vh;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

.loading-spinner.small {
  width: 30px;
  height: 30px;
  border-width: 3px;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #fee2e2;
  color: #b91c1c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
}

.error-state h2 {
  font-size: 1.75rem;
  color: #1e293b;
  margin: 0 0 1rem;
}

.error-state p {
  color: #64748b;
  max-width: 500px;
  margin: 0 0 2rem;
}

.primary-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
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
  padding: 0.75rem 1.5rem;
  background-color: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.secondary-btn.active {
  background-color: #dbeafe;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.profile-header {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background-color: white;
  margin-top: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.profile-cover {
  height: 200px;
  position: relative;
}

.profile-header-content {
  padding: 0 2rem 2rem;
  position: relative;
  display: flex;
  flex-wrap: wrap;
}

.profile-avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background-color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: 600;
  color: white;
  border: 6px solid white;
  margin-top: -75px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-info {
  flex: 1;
  padding: 1.5rem 2rem 0;
  min-width: 0;
}

.profile-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.profile-name {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.profile-role {
  padding: 0.35rem 0.75rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
}

.role-admin {
  background-color: #ef4444;
}

.role-moderator {
  background-color: #8b5cf6;
}

.role-user {
  background-color: #10b981;
}

.profile-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.profile-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
}

.profile-bio {
  color: #475569;
  line-height: 1.7;
  max-width: 800px;
}

.profile-bio.empty {
  font-style: italic;
  color: #94a3b8;
}

.profile-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  margin-left: auto;
  align-self: flex-end;
}

.profile-tabs {
  display: flex;
  background-color: white;
  border-radius: 10px;
  margin-top: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.tab-btn {
  padding: 1.25rem 2rem;
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  white-space: nowrap;
}

.tab-btn:after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #3b82f6;
}

.tab-btn.active:after {
  background-color: #3b82f6;
}

.tab-btn:hover:not(.active) {
  color: #334155;
  background-color: #f8fafc;
}

.tab-content {
  margin-top: 2rem;
}

.loading-tab, .empty-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  text-align: center;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.loading-tab p, .empty-tab p {
  margin: 0;
  color: #64748b;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #94a3b8;
}

.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  text-align: center;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.coming-soon-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
}

.coming-soon h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin: 0 0 1rem;
}

.coming-soon p {
  color: #64748b;
  max-width: 500px;
  margin: 0;
}

.posts-list {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.post-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
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
  justify-content: space-between;
  align-items: center;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.post-category {
  padding: 0.35rem 0.75rem;
  background-color: #f1f5f9;
  border-radius: 4px;
  font-size: 0.825rem;
  font-weight: 500;
  color: #475569;
}

.post-date {
  font-size: 0.825rem;
  color: #64748b;
}

.post-title {
  font-size: 1.25rem;
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
  font-size: 0.95rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-footer {
  display: flex;
  align-items: center;
  margin-top: auto;
}

.post-stats {
  display: flex;
  gap: 1.25rem;
}

.post-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
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

/* Responsive design */
@media (max-width: 1024px) {
  .profile-header-content {
    padding: 0 1.5rem 1.5rem;
  }
  
  .profile-info {
    padding: 1.5rem 0 0;
  }
  
  .profile-actions {
    margin-top: 1.5rem;
  }
  
  .post-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .profile-avatar {
    width: 120px;
    height: 120px;
    font-size: 2.5rem;
    margin-top: -60px;
  }
  
  .profile-name {
    font-size: 1.75rem;
  }
  
  .profile-stats {
    gap: 1.5rem;
  }
  
  .tab-btn {
    padding: 1rem 1.5rem;
  }
  
  .post-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .profile-cover {
    height: 150px;
  }
  
  .profile-info {
    width: 100%;
  }
  
  .profile-meta {
    margin-bottom: 1rem;
  }
  
  .profile-actions {
    width: 100%;
    margin-left: 0;
  }
  
  .profile-actions .primary-btn,
  .profile-actions .secondary-btn {
    flex: 1;
    text-align: center;
  }
  
  .profile-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .posts-list {
    padding: 1.5rem;
  }
}
</style>
