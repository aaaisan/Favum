<template>
  <div class="categories-page">
    <div class="header-section">
      <div class="container">
        <h1 class="main-title">话题分类</h1>
        <p class="main-subtitle">探索各种不同的话题分类，查找你感兴趣的内容</p>
      </div>
    </div>
    
    <div class="container main-content">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <template v-else>
        <div class="search-section">
          <div class="search-box">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索分类..." 
              @input="handleSearch"
            />
            <button class="search-btn">🔍</button>
          </div>
        </div>
        
        <div v-if="filteredCategories.length === 0" class="empty-state">
          <div class="empty-icon">🔍</div>
          <p>没有找到匹配"{{ searchQuery }}"的分类</p>
          <button class="clear-btn" @click="clearSearch">清除搜索</button>
        </div>
        
        <div v-else class="categories-grid">
          <router-link 
            v-for="category in filteredCategories" 
            :key="category.id"
            :to="`/categories/${category.id}`"
            class="category-card"
            :style="{ borderColor: category.color }"
          >
            <div class="category-header" :style="{ backgroundColor: category.color }">
              <div class="category-icon" v-if="category.icon">{{ category.icon }}</div>
              <div class="category-icon" v-else>📚</div>
            </div>
            
            <div class="category-content">
              <h2 class="category-name">{{ category.name }}</h2>
              <p class="category-description" v-if="category.description">
                {{ category.description }}
              </p>
              <p class="category-description" v-else>
                暂无描述
              </p>
              
              <div class="category-stats">
                <div class="stat-item">
                  <i class="icon">📝</i>
                  <span>{{ category.postCount }} 帖子</span>
                </div>
                <div class="stat-item">
                  <i class="icon">👥</i>
                  <span>{{ category.userCount }} 参与者</span>
                </div>
              </div>
            </div>
            
            <div class="category-footer">
              <span class="latest-post">最新: {{ formatDate(category.lastPostAt) }}</span>
              <span class="view-category">浏览分类 →</span>
            </div>
          </router-link>
        </div>
      </template>
      
      <div class="featured-section">
        <h2 class="section-title">热门讨论</h2>
        
        <div class="featured-posts">
          <div class="post-card" v-for="post in featuredPosts" :key="post.id">
            <div class="post-header">
              <div class="user-avatar">{{ getUserInitials(post.author) }}</div>
              <div class="post-meta">
                <div class="post-author">{{ post.author }}</div>
                <div class="post-date">{{ formatDate(post.created_at) }}</div>
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
                  <span>{{ post.views }}</span>
                </div>
                <div class="stat-item">
                  <i class="icon">💬</i>
                  <span>{{ post.comments_count }}</span>
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
import { ref, computed, onMounted } from 'vue'

const isLoading = ref(true)
const searchQuery = ref('')
const loadError = ref('')

// Define proper types for our data
interface Category {
  id: number
  name: string
  description: string | null
  color?: string
  icon?: string
  postCount: number
  userCount: number
  lastPostAt: string | null
}

interface Post {
  id: number
  title: string
  author: string
  category: string
  excerpt: string
  created_at: string
  views: number
  comments_count: number
}

const categories = ref<Category[]>([])
const featuredPosts = ref<Post[]>([])

// Filtered categories based on search query
const filteredCategories = computed(() => {
  if (!searchQuery.value) return categories.value
  
  const query = searchQuery.value.toLowerCase()
  return categories.value.filter(category => 
    category.name.toLowerCase().includes(query) || 
    (category.description && category.description.toLowerCase().includes(query))
  )
})

// Format date from ISO string
const formatDate = (dateString: string | null) => {
  if (!dateString) return '无记录'
  
  const date = new Date(dateString)
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

// Get user initials from name
const getUserInitials = (name: string) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

// Search handler
const handleSearch = () => {
  // No need for API call since we filter client-side
  console.log('搜索:', searchQuery.value)
}

// Clear search
const clearSearch = () => {
  searchQuery.value = ''
}

// Fetch categories from API
const fetchCategories = async () => {
  isLoading.value = true
  loadError.value = ''
  
  try {
    const response = await fetch('/api/categories')
    if (!response.ok) {
      throw new Error('Failed to fetch categories')
    }
    
    const data = await response.json()
    // Map the API response to our component's expected format
    categories.value = data.map((category: any) => ({
      id: category.id,
      name: category.name,
      description: category.description,
      color: category.color || getRandomColor(category.id),
      icon: category.icon || '📚',
      postCount: category.post_count || 0,
      userCount: category.user_count || 0,
      lastPostAt: category.last_post_at
    }))
  } catch (error) {
    console.error('Error fetching categories:', error)
    loadError.value = 'Failed to load categories. Please try again.'
  } finally {
    isLoading.value = false
  }
}

// Fetch featured posts from API
const fetchFeaturedPosts = async () => {
  try {
    const response = await fetch('/api/posts/featured')
    if (!response.ok) {
      throw new Error('Failed to fetch featured posts')
    }
    
    const data = await response.json()
    // Map the API response to our component's expected format
    featuredPosts.value = data.map((post: any) => ({
      id: post.id,
      title: post.title,
      author: post.author?.username || '未知作者',
      category: getCategoryName(post.category_id),
      excerpt: getExcerpt(post.content),
      created_at: post.created_at,
      views: post.views || 0,
      comments_count: post.comments?.length || 0
    }))
  } catch (error) {
    console.error('Error fetching featured posts:', error)
  }
}

// Helper to get category name by ID
const getCategoryName = (categoryId: number) => {
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : '未分类'
}

// Helper to get excerpt from content
const getExcerpt = (content: string) => {
  if (!content) return ''
  // Strip HTML tags and get first 150 characters
  const plainText = content.replace(/<[^>]*>/g, '')
  return plainText.length > 150 ? plainText.substring(0, 150) + '...' : plainText
}

// Generate a random color based on category ID for visual consistency
const getRandomColor = (id: number) => {
  const colors = [
    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
    '#9b59b6', '#16a085', '#f1c40f', '#e67e22'
  ]
  return colors[id % colors.length]
}

// Component mounted - fetch data
onMounted(() => {
  fetchCategories()
  fetchFeaturedPosts()
})
</script>

<style scoped>
.categories-page {
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
  padding: 4rem 0 3rem;
  text-align: center;
  margin-bottom: 2.5rem;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0 0 1rem;
  letter-spacing: -0.025em;
}

.main-subtitle {
  font-size: 1.1rem;
  font-weight: 400;
  color: #cbd5e1;
  max-width: 700px;
  margin: 0 auto;
}

.main-content {
  margin-bottom: 4rem;
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

.search-section {
  margin-bottom: 2.5rem;
}

.search-box {
  position: relative;
  max-width: 600px;
  margin: 0 auto;
}

.search-box input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.search-btn {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.2rem;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 4rem 0;
  color: #64748b;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #94a3b8;
}

.clear-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #dbeafe;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background-color: #dbeafe;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 4rem;
}

.category-card {
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-top: 4px solid;
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  text-decoration: none;
  height: 100%;
}

.category-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.category-header {
  padding: 2rem 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.category-icon {
  font-size: 3rem;
  color: white;
}

.category-content {
  padding: 1.5rem;
  flex: 1;
}

.category-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.75rem;
}

.category-description {
  color: #475569;
  margin: 0 0 1.5rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.category-stats {
  display: flex;
  justify-content: space-between;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.95rem;
}

.category-footer {
  padding: 1rem 1.5rem;
  background-color: #f8fafc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #64748b;
  font-size: 0.875rem;
}

.view-category {
  color: #3b82f6;
  font-weight: 500;
  transition: transform 0.2s;
}

.category-card:hover .view-category {
  transform: translateX(5px);
}

.featured-section {
  margin-top: 4rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 2rem;
  text-align: center;
}

.featured-posts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.post-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
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

/* Responsive design */
@media (max-width: 1024px) {
  .categories-grid, .featured-posts {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .header-section {
    padding: 3rem 0 2.5rem;
  }
  
  .main-title {
    font-size: 2rem;
  }
  
  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.25rem;
  }
  
  .featured-posts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .categories-grid {
    grid-template-columns: 1fr;
  }
  
  .category-card {
    max-width: 400px;
    margin: 0 auto;
  }
}
</style> 