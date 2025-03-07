<template>
  <DashboardLayout>
    <div class="dashboard-overview">
      <div class="dashboard-header">
        <h1>仪表盘</h1>
        <div class="date-display">{{ formattedDate }}</div>
      </div>
      
      <div class="stats-summary">
        <div class="stats-card total-users">
          <div class="stats-icon">👥</div>
          <div class="stats-content">
            <div class="stats-value">{{ stats.totalUsers }}</div>
            <div class="stats-label">总用户数</div>
            <div class="stats-change" :class="{ 'positive': stats.newUsersChange > 0, 'negative': stats.newUsersChange < 0 }">
              {{ stats.newUsersChange > 0 ? '+' : '' }}{{ stats.newUsersChange }}%
            </div>
          </div>
        </div>
        
        <div class="stats-card total-posts">
          <div class="stats-icon">📝</div>
          <div class="stats-content">
            <div class="stats-value">{{ stats.totalPosts }}</div>
            <div class="stats-label">总帖子数</div>
            <div class="stats-change" :class="{ 'positive': stats.newPostsChange > 0, 'negative': stats.newPostsChange < 0 }">
              {{ stats.newPostsChange > 0 ? '+' : '' }}{{ stats.newPostsChange }}%
            </div>
          </div>
        </div>
        
        <div class="stats-card total-comments">
          <div class="stats-icon">💬</div>
          <div class="stats-content">
            <div class="stats-value">{{ stats.totalComments }}</div>
            <div class="stats-label">总评论数</div>
            <div class="stats-change" :class="{ 'positive': stats.newCommentsChange > 0, 'negative': stats.newCommentsChange < 0 }">
              {{ stats.newCommentsChange > 0 ? '+' : '' }}{{ stats.newCommentsChange }}%
            </div>
          </div>
        </div>
        
        <div class="stats-card daily-active">
          <div class="stats-icon">🔥</div>
          <div class="stats-content">
            <div class="stats-value">{{ stats.dailyActiveUsers }}</div>
            <div class="stats-label">日活跃用户</div>
            <div class="stats-change" :class="{ 'positive': stats.dailyActiveChange > 0, 'negative': stats.dailyActiveChange < 0 }">
              {{ stats.dailyActiveChange > 0 ? '+' : '' }}{{ stats.dailyActiveChange }}%
            </div>
          </div>
        </div>
      </div>
      
      <div class="dashboard-content">
        <div class="content-main">
          <div class="recent-posts panel">
            <div class="panel-header">
              <h2>最近的帖子</h2>
              <router-link to="/dashboard/posts" class="view-all">查看全部 →</router-link>
            </div>
            
            <div class="posts-list">
              <div v-if="isLoading" class="loading">加载中...</div>
              <div v-else-if="recentPosts.length === 0" class="empty-message">暂无帖子</div>
              <div v-else class="table-responsive">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>标题</th>
                      <th>作者</th>
                      <th>分类</th>
                      <th>状态</th>
                      <th>发布时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="post in recentPosts" :key="post.id">
                      <td class="title-cell">
                        <router-link :to="`/posts/${post.id}`" class="post-title">{{ post.title }}</router-link>
                      </td>
                      <td>{{ post.author }}</td>
                      <td>
                        <span class="category-badge" :style="{ backgroundColor: post.categoryColor + '20', color: post.categoryColor }">
                          {{ post.category }}
                        </span>
                      </td>
                      <td>
                        <span class="status-badge" :class="post.status">{{ getStatusText(post.status) }}</span>
                      </td>
                      <td>{{ formatDate(post.createdAt) }}</td>
                      <td>
                        <div class="actions">
                          <button class="action-btn view" @click="viewPost(post)">查看</button>
                          <button v-if="post.status === 'pending'" class="action-btn approve" @click="approvePost(post)">批准</button>
                          <button class="action-btn edit" @click="editPost(post)">编辑</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div class="activity-chart panel">
            <div class="panel-header">
              <h2>活跃度统计</h2>
              <div class="chart-period-selector">
                <button 
                  v-for="period in ['day', 'week', 'month']" 
                  :key="period"
                  :class="{ active: chartPeriod === period }"
                  @click="chartPeriod = period"
                >
                  {{ getPeriodText(period) }}
                </button>
              </div>
            </div>
            
            <div class="chart-container">
              <div class="chart-placeholder">
                <div class="chart-message">此处将显示活跃度图表</div>
                <div class="chart-bars">
                  <div class="chart-bar" v-for="n in 7" :key="n" :style="{ height: `${Math.random() * 70 + 30}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="content-side">
          <div class="pending-items panel">
            <div class="panel-header">
              <h2>待处理事项</h2>
            </div>
            
            <div class="pending-list">
              <div class="pending-item">
                <div class="pending-count">{{ pendingItems.reports }}</div>
                <div class="pending-info">
                  <div class="pending-title">举报</div>
                  <div class="pending-desc">需要审核的用户举报</div>
                </div>
                <router-link to="/dashboard/reports" class="pending-action">处理</router-link>
              </div>
              
              <div class="pending-item">
                <div class="pending-count">{{ pendingItems.posts }}</div>
                <div class="pending-info">
                  <div class="pending-title">待审帖子</div>
                  <div class="pending-desc">等待审核的新帖子</div>
                </div>
                <router-link to="/dashboard/posts" class="pending-action">审核</router-link>
              </div>
              
              <div class="pending-item">
                <div class="pending-count">{{ pendingItems.comments }}</div>
                <div class="pending-info">
                  <div class="pending-title">待审评论</div>
                  <div class="pending-desc">等待审核的评论</div>
                </div>
                <router-link to="/dashboard/comments" class="pending-action">审核</router-link>
              </div>
            </div>
          </div>
          
          <div class="popular-categories panel">
            <div class="panel-header">
              <h2>热门分类</h2>
              <router-link to="/dashboard/categories" class="view-all">查看全部 →</router-link>
            </div>
            
            <div class="categories-list">
              <div v-for="category in popularCategories" :key="category.id" class="category-item">
                <div class="category-info">
                  <div class="category-icon" :style="{ backgroundColor: category.color }">
                    {{ category.icon }}
                  </div>
                  <div class="category-name">{{ category.name }}</div>
                </div>
                <div class="category-count">{{ category.postCount }} 帖子</div>
              </div>
            </div>
          </div>
          
          <div class="recent-users panel">
            <div class="panel-header">
              <h2>最新用户</h2>
              <router-link to="/dashboard/users" class="view-all">查看全部 →</router-link>
            </div>
            
            <div class="users-list">
              <div v-for="user in recentUsers" :key="user.id" class="user-item">
                <div class="user-avatar">
                  <img v-if="user.avatar" :src="user.avatar" :alt="user.username" />
                  <div v-else class="avatar-placeholder">{{ getUserInitials(user.username) }}</div>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ user.username }}</div>
                  <div class="user-date">注册于 {{ formatDate(user.createdAt) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '../components/DashboardLayout.vue'

const router = useRouter()
const isLoading = ref(true)
const chartPeriod = ref('week')

// 获取当前日期
const formattedDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

// 统计数据
const stats = ref({
  totalUsers: 1258,
  newUsersChange: 5.2,
  totalPosts: 3642,
  newPostsChange: 12.8,
  totalComments: 8976,
  newCommentsChange: 8.4,
  dailyActiveUsers: 324,
  dailyActiveChange: -2.1
})

// 待处理事项
const pendingItems = ref({
  reports: 8,
  posts: 15,
  comments: 27
})

// 最近的帖子
const recentPosts = ref([
  {
    id: 1,
    title: '如何使用 Vue.js 构建响应式 Web 应用程序',
    author: '张三',
    category: 'Vue.js',
    categoryColor: '#4fc08d',
    status: 'published',
    createdAt: new Date(Date.now() - 86400000 * 1) // 1天前
  },
  {
    id: 2,
    title: 'React Hooks 完全指南',
    author: '李四',
    category: 'React',
    categoryColor: '#61dafb',
    status: 'pending',
    createdAt: new Date(Date.now() - 86400000 * 1.5) // 1.5天前
  },
  {
    id: 3,
    title: 'TypeScript 高级类型系统详解',
    author: '王五',
    category: 'TypeScript',
    categoryColor: '#3178c6',
    status: 'published',
    createdAt: new Date(Date.now() - 86400000 * 2) // 2天前
  },
  {
    id: 4,
    title: '现代 CSS 布局技巧',
    author: '赵六',
    category: 'CSS',
    categoryColor: '#264de4',
    status: 'published',
    createdAt: new Date(Date.now() - 86400000 * 2.5) // 2.5天前
  },
  {
    id: 5,
    title: 'JavaScript 异步编程最佳实践',
    author: '孙七',
    category: 'JavaScript',
    categoryColor: '#f7df1e',
    status: 'pending',
    createdAt: new Date(Date.now() - 86400000 * 3) // 3天前
  }
])

// 热门分类
const popularCategories = ref([
  {
    id: 1,
    name: 'JavaScript',
    icon: 'JS',
    color: '#f7df1e',
    postCount: 428
  },
  {
    id: 2,
    name: 'Vue.js',
    icon: 'Vue',
    color: '#4fc08d',
    postCount: 312
  },
  {
    id: 3,
    name: 'React',
    icon: 'R',
    color: '#61dafb',
    postCount: 287
  },
  {
    id: 4,
    name: 'CSS',
    icon: 'CSS',
    color: '#264de4',
    postCount: 196
  }
])

// 最新用户
const recentUsers = ref([
  {
    id: 1,
    username: '陈小明',
    avatar: null,
    createdAt: new Date(Date.now() - 86400000 * 0.5) // 0.5天前
  },
  {
    id: 2,
    username: '林小华',
    avatar: null,
    createdAt: new Date(Date.now() - 86400000 * 1) // 1天前
  },
  {
    id: 3,
    username: '张小红',
    avatar: null,
    createdAt: new Date(Date.now() - 86400000 * 1.2) // 1.2天前
  },
  {
    id: 4,
    username: '刘小阳',
    avatar: null,
    createdAt: new Date(Date.now() - 86400000 * 1.8) // 1.8天前
  }
])

// 获取用户名首字母
const getUserInitials = (username: string): string => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    published: '已发布',
    pending: '待审核',
    draft: '草稿',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

// 获取时间段文本
const getPeriodText = (period: string): string => {
  const periodMap: Record<string, string> = {
    day: '日',
    week: '周',
    month: '月'
  }
  return periodMap[period] || period
}

// 格式化日期
const formatDate = (date: Date): string => {
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 查看帖子
const viewPost = (post: any) => {
  router.push(`/posts/${post.id}`)
}

// 编辑帖子
const editPost = (post: any) => {
  router.push(`/dashboard/posts/edit/${post.id}`)
}

// 批准帖子
const approvePost = (post: any) => {
  // 实际应用中这里会调用API
  console.log('批准帖子:', post.id)
  
  // 更新状态
  const index = recentPosts.value.findIndex(p => p.id === post.id)
  if (index !== -1) {
    recentPosts.value[index].status = 'published'
  }
  
  // 减少待处理数量
  pendingItems.value.posts--
}

// 组件挂载时加载数据
onMounted(() => {
  // 模拟API请求
  setTimeout(() => {
    isLoading.value = false
  }, 1000)
})
</script>

<style scoped>
.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 1.75rem;
  color: #1e293b;
  font-weight: 600;
}

.date-display {
  font-size: 1rem;
  color: #64748b;
  font-weight: 500;
  padding: 0.5rem 1rem;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.stats-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stats-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.stats-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  border-radius: 10px;
  background-color: #f1f5f9;
  flex-shrink: 0;
}

.total-users .stats-icon {
  background-color: #e0f2fe;
  color: #0369a1;
}

.total-posts .stats-icon {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.total-comments .stats-icon {
  background-color: #f3e8ff;
  color: #7e22ce;
}

.daily-active .stats-icon {
  background-color: #fee2e2;
  color: #b91c1c;
}

.stats-content {
  flex: 1;
}

.stats-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stats-label {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.stats-change {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}

.stats-change.positive {
  background-color: #dcfce7;
  color: #166534;
}

.stats-change.negative {
  background-color: #fee2e2;
  color: #b91c1c;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.content-side {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.panel {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
  font-weight: 600;
}

.view-all {
  font-size: 0.85rem;
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.view-all:hover {
  color: #2980b9;
}

.posts-list, .chart-container {
  padding: 1rem 1.5rem;
}

.loading, .empty-message {
  padding: 3rem 1rem;
  text-align: center;
  color: #64748b;
  font-style: italic;
}

.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  background-color: #f8fafc;
  color: #1e293b;
  font-weight: 600;
  font-size: 0.85rem;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.9rem;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background-color: #f8fafc;
}

.title-cell {
  max-width: 300px;
}

.post-title {
  color: #1e293b;
  text-decoration: none;
  font-weight: 500;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-title:hover {
  color: #3498db;
}

.category-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
}

.status-badge.published {
  background-color: #dcfce7;
  color: #166534;
}

.status-badge.pending {
  background-color: #fef3c7;
  color: #92400e;
}

.status-badge.draft {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-badge.rejected {
  background-color: #fee2e2;
  color: #b91c1c;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.35rem 0.5rem;
  font-size: 0.75rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.action-btn.view {
  background-color: #e0f2fe;
  color: #0369a1;
}

.action-btn.view:hover {
  background-color: #bae6fd;
}

.action-btn.edit {
  background-color: #fef9c3;
  color: #854d0e;
}

.action-btn.edit:hover {
  background-color: #fef08a;
}

.action-btn.approve {
  background-color: #dcfce7;
  color: #166534;
}

.action-btn.approve:hover {
  background-color: #bbf7d0;
}

.chart-period-selector {
  display: flex;
  gap: 0.5rem;
}

.chart-period-selector button {
  padding: 0.35rem 0.75rem;
  background-color: #f1f5f9;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s;
}

.chart-period-selector button.active {
  background-color: #3498db;
  color: white;
}

.chart-period-selector button:hover:not(.active) {
  background-color: #e2e8f0;
}

.chart-placeholder {
  height: 250px;
  background-color: #f8fafc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.chart-message {
  color: #64748b;
  font-style: italic;
  margin-bottom: 2rem;
  z-index: 2;
}

.chart-bars {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 70%;
  padding: 0 2rem;
  opacity: 0.3;
}

.chart-bar {
  width: 10%;
  background-color: #3498db;
  border-radius: 4px 4px 0 0;
}

.pending-list {
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pending-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
}

.pending-count {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  background-color: #3498db;
  border-radius: 8px;
  flex-shrink: 0;
}

.pending-item:nth-child(1) .pending-count {
  background-color: #ef4444;
}

.pending-item:nth-child(2) .pending-count {
  background-color: #f59e0b;
}

.pending-item:nth-child(3) .pending-count {
  background-color: #8b5cf6;
}

.pending-info {
  flex: 1;
}

.pending-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.pending-desc {
  font-size: 0.85rem;
  color: #64748b;
}

.pending-action {
  padding: 0.35rem 0.75rem;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  color: #3498db;
  font-weight: 500;
  font-size: 0.85rem;
  text-decoration: none;
  transition: all 0.2s;
}

.pending-action:hover {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.categories-list, .users-list {
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  border-radius: 8px;
  background-color: #f8fafc;
  transition: all 0.2s;
}

.category-item:hover {
  background-color: #f1f5f9;
  transform: translateX(5px);
}

.category-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.85rem;
  border-radius: 6px;
}

.category-name {
  font-weight: 500;
  color: #1e293b;
}

.category-count {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
  background-color: #f8fafc;
  transition: all 0.2s;
}

.user-item:hover {
  background-color: #f1f5f9;
  transform: translateX(5px);
}

.user-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  overflow: hidden;
  background-color: #3498db;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.user-date {
  font-size: 0.75rem;
  color: #64748b;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-summary {
    grid-template-columns: 1fr;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style> 