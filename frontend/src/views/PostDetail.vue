<template>
  <div class="post-detail-page">
    <div class="container">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="errorMessage" class="error-state">
        <div class="error-icon">!</div>
        <h2>加载失败</h2>
        <p>{{ errorMessage }}</p>
        <div class="error-details">
          <p>可能的原因：</p>
          <ul>
            <li>帖子可能不存在或已被删除</li>
            <li>后端服务未启动或暂时不可用</li>
            <li>网络连接问题</li>
          </ul>
        </div>
        <div class="error-actions">
          <button class="secondary-btn" @click="fetchPost">重试</button>
          <router-link to="/" class="primary-btn">返回首页</router-link>
        </div>
      </div>
      
      <template v-else-if="post">
        <div class="content-layout">
          <div class="post-container">
            <div class="breadcrumbs">
              <router-link to="/" class="breadcrumb-item">首页</router-link>
              <span class="separator">/</span>
              <router-link :to="`/categories/${post.category?.id}`" class="breadcrumb-item">
                {{ post.category?.name || '未分类' }}
              </router-link>
              <span class="separator">/</span>
              <span class="breadcrumb-current">{{ post.title }}</span>
            </div>
            
            <div class="post-header">
              <h1 class="post-title">{{ post.title }}</h1>
              
              <div class="post-meta">
                <div class="author-info">
                  <div class="author-avatar">{{ getUserInitials(`用户ID:${post.author_id}`) }}</div>
                  <div class="author-details">
                    <router-link :to="`/users/${post.author_id}`" class="author-name">
                      用户ID: {{ post.author_id }}
                    </router-link>
                    <div class="post-dates">
                      <span>发布于 {{ formatDate(post.created_at) }}</span>
                      <span v-if="post.updated_at !== post.created_at" class="updated-date">
                        · 更新于 {{ formatDate(post.updated_at) }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="category-badge" :style="{ backgroundColor: getCategoryColor(post.category) }">
                  {{ post.category?.name || '未分类' }}
                </div>
              </div>
            </div>
            
            <div class="post-content">
              <div class="content-text">
                {{ post.content }}
              </div>
              
              <div class="post-stats">
                <div class="stat-item">
                  <i class="icon">👁️</i>
                  <span>{{ post.view_count || 0 }} 次浏览</span>
                </div>
                <div class="stat-item">
                  <i class="icon">💬</i>
                  <span>{{ post.comments?.length || 0 }} 条评论</span>
                </div>
              </div>
              
              <div class="post-tags" v-if="post.tags && post.tags.length > 0">
                <div class="tags-label">标签:</div>
                <div class="tags-list">
                  <router-link 
                    v-for="tag in post.tags" 
                    :key="tag.id"
                    :to="`/tags/${tag.id}`"
                    class="tag"
                  >
                    {{ tag.name }}
                  </router-link>
                </div>
              </div>
            </div>
            
            <div class="post-actions">
              <div class="vote-buttons">
                <button 
                  class="vote-btn upvote"
                  :class="{ active: userVote === 'upvote' }"
                  @click="handleVote('upvote')"
                >
                  <span class="vote-icon">👍</span>
                  <span class="vote-count">{{ post.vote_count || 0 }}</span>
                </button>
                
                <button 
                  class="vote-btn downvote"
                  :class="{ active: userVote === 'downvote' }"
                  @click="handleVote('downvote')"
                >
                  <span class="vote-icon">👎</span>
                </button>
              </div>
              
              <div class="share-buttons">
                <button class="action-btn" @click="sharePost">
                  <span class="action-icon">🔗</span>
                  <span class="action-text">分享</span>
                </button>
                
                <button class="action-btn" @click="reportPost">
                  <span class="action-icon">⚠️</span>
                  <span class="action-text">举报</span>
                </button>
              </div>
            </div>
            
            <div class="comments-section">
              <h2 class="section-title">评论 ({{ post.comments?.length || 0 }})</h2>
              
              <div class="comment-form">
                <textarea
                  placeholder="写下你的评论..."
                  rows="3"
                  class="comment-input"
                  v-model="commentText"
                ></textarea>
                <button class="primary-btn" @click="submitComment" :disabled="!commentText.trim()">
                  发表评论
                </button>
              </div>
              
              <div class="comments-list">
                <div v-if="!comments || comments.length === 0" class="no-comments">
                  暂无评论，快来发表第一条评论吧！
                </div>
                
                <div v-for="comment in comments" :key="comment.id" class="comment-item">
                  <div class="comment-user">
                    <div class="user-avatar">{{ getUserInitials(`用户ID:${comment.user_id}`) }}</div>
                    <div class="user-info">
                      <div class="user-name">用户ID: {{ comment.user_id }}</div>
                      <div class="comment-date">{{ formatDate(comment.created_at) }}</div>
                    </div>
                  </div>
                  <div class="comment-content">
                    {{ comment.content }}
                  </div>
                  <div class="comment-actions">
                    <button class="comment-action">回复</button>
                    <button class="comment-action">点赞</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="sidebar">
            <div class="sidebar-section">
              <h3>作者信息</h3>
              <div class="author-card">
                <div class="author-avatar large">{{ getUserInitials(`用户ID:${post.author_id}`) }}</div>
                <div class="author-name">用户ID: {{ post.author_id }}</div>
                <div class="author-stats">
                  <div class="stat-item">
                    <div class="stat-value">42</div>
                    <div class="stat-label">帖子</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">128</div>
                    <div class="stat-label">被赞</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">16</div>
                    <div class="stat-label">评论</div>
                  </div>
                </div>
                <router-link :to="`/users/${post.author_id}`" class="view-profile-btn">
                  查看个人资料
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watchEffect, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostDetail } from '../composables/usePostDetail'
import { formatDate } from '../utils/format'

const route = useRoute()
const router = useRouter()
console.log('PostDetail组件初始化, 路由参数:', route.params)

// 确保 postId 正确解析为数字
const postId = computed(() => {
  console.log('计算postId，路由参数:', JSON.stringify(route.params))
  console.log('路由参数中的原始ID:', route.params.id, '类型:', typeof route.params.id)
  
  // 防止路由参数是对象的情况
  let idStr: any = route.params.id
  if (typeof idStr === 'object') {
    console.error('警告: 路由ID参数是一个对象:', JSON.stringify(idStr))
    if (idStr && typeof idStr === 'object' && 'id' in idStr) {
      console.log('从对象中提取id属性')
      idStr = idStr.id
    } else {
      console.error('尝试将对象转换为字符串')
      idStr = String(idStr)
    }
  }
  
  // 确保转换为字符串
  const idAsString = String(idStr)
  console.log('转换为字符串后的ID:', idAsString)
  
  // 转换为数字
  const id = Number(idAsString)
  console.log('转换后的帖子ID:', id, '类型:', typeof id)
  
  if (isNaN(id) || id <= 0) {
    // 如果ID无效，重定向到首页
    console.error('无效的帖子ID，重定向到首页')
    router.push('/')
    return 0
  }
  return id
})
const commentText = ref('')

// 获取用户名缩写
const getUserInitials = (username: string | undefined) => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

// 获取分类颜色
const getCategoryColor = (category: any) => {
  if (!category || !category.color) return '#3b82f6'
  return category.color
}

// 使用帖子详情组合式函数 - 直接传递 postId 计算属性
console.log('准备调用usePostDetail, postId:', postId.value)
const {
  post,
  userVote,
  isLoading,
  errorMessage,
  fetchPost,
  handleVote,
  addComment
} = usePostDetail(postId)
console.log('usePostDetail返回结果, isLoading:', isLoading.value, 'errorMessage:', errorMessage.value)

// 计算评论列表
const comments = computed(() => post.value?.comments || [])

// 分享帖子
const sharePost = () => {
  // 实际应用中这里会调用分享API或复制链接
  alert('链接已复制到剪贴板')
}

// 举报帖子
const reportPost = () => {
  // 实际应用中这里会打开举报模态框
  alert('举报功能即将上线')
}

// 提交评论
const submitComment = async () => {
  if (!commentText.value.trim()) return
  
  // 首先检查用户是否登录
  const token = localStorage.getItem('token')
  if (!token) {
    console.log('用户未登录，需要先登录才能评论')
    
    // 存储当前状态，以便登录后返回
    try {
      sessionStorage.setItem('returnPath', router.currentRoute.value.fullPath)
      sessionStorage.setItem('pendingAction', 'comment')
      sessionStorage.setItem('pendingComment', commentText.value)
    } catch (e) {
      console.error('保存评论状态失败:', e)
    }
    
    // 导航到登录页
    router.push('/login')
    return
  }
  
  // 使用我们的composable函数中的addComment方法
  const success = await addComment(commentText.value)
  
  // 如果评论发表成功，清空输入框
  if (success) {
    commentText.value = ''
  }
}

// onMounted中添加更详细的日志
onMounted(() => {
  console.log('---------- PostDetail组件已挂载 ----------')
  console.log('当前postId:', postId.value, '类型:', typeof postId.value)
  console.log('isLoading状态:', isLoading.value)
  console.log('errorMessage:', errorMessage.value)
  console.log('post数据:', post.value)
  console.log('------------------------------------------')
  
  // 设置定时器检查加载状态 - 改为只检查一次，不重复触发请求
  let checkInterval: number | null = null;
  
  // 只在开发环境中启用状态监控，减少不必要的请求和日志
  if (process.env.NODE_ENV === 'development') {
    checkInterval = window.setInterval(() => {
      console.log('定时检查 - isLoading:', isLoading.value, 'errorMessage:', errorMessage.value, 'post:', post.value ? '有数据' : '无数据')
      if (!isLoading.value || errorMessage.value || post.value) {
        if (checkInterval !== null) {
          clearInterval(checkInterval)
          checkInterval = null
          console.log('停止定时检查，状态已确定')
        }
      }
    }, 1000)
    
    // 设置超时检查，确保不会无限等待
    const timeoutCheck = window.setTimeout(() => {
      if (isLoading.value) {
        console.warn('获取帖子超时，可能存在网络问题')
        console.warn('当前状态 - isLoading:', isLoading.value, 'errorMessage:', errorMessage.value)
      } else if (errorMessage.value) {
        console.error('获取帖子出错:', errorMessage.value)
      } else if (!post.value) {
        console.warn('获取帖子成功但数据为空')
      }
      
      if (checkInterval !== null) {
        clearInterval(checkInterval)
        checkInterval = null
      }
    }, 5000)
    
    // 确保在组件卸载时清除定时器，防止内存泄漏
    onUnmounted(() => {
      if (checkInterval !== null) {
        clearInterval(checkInterval)
        checkInterval = null
      }
      clearTimeout(timeoutCheck)
    })
  }
})

// 添加路由参数变化监听
watchEffect(() => {
  // 当路由参数变化时，记录并重新获取数据
  const currentId = route.params.id
  console.log('路由参数变化检测，当前ID:', currentId)
  
  // 不需要手动调用fetchPost，因为postId计算属性会变化，
  // 而usePostDetail中的watchEffect会自动触发数据获取
})
</script>

<style scoped>
.post-detail-page {
  width: 100%;
  background-color: #f8fafc;
  min-height: 100vh;
  padding: 2rem 0 4rem;
}

.container {
  max-width: 1400px;
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

.error-details {
  margin-bottom: 2rem;
}

.error-details p {
  font-size: 0.95rem;
  color: #64748b;
  margin: 0 0 0.5rem;
}

.error-details ul {
  list-style: disc;
  padding-left: 20px;
}

.error-details li {
  font-size: 0.95rem;
  color: #64748b;
}

.error-actions {
  display: flex;
  gap: 1rem;
}

.secondary-btn {
  padding: 0.75rem 1.5rem;
  background-color: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background-color: #f1f5f9;
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

.primary-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.content-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 2.5rem;
  align-items: start;
}

.post-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.875rem;
  color: #64748b;
  overflow-x: auto;
  white-space: nowrap;
}

.breadcrumb-item {
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #3b82f6;
}

.breadcrumb-current {
  color: #1e293b;
  font-weight: 500;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.separator {
  margin: 0 0.5rem;
  color: #cbd5e1;
}

.post-header {
  padding: 2rem 2rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.post-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 1.5rem;
  line-height: 1.3;
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.author-avatar {
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
  flex-shrink: 0;
}

.author-avatar.large {
  width: 80px;
  height: 80px;
  font-size: 2rem;
}

.author-details {
  display: flex;
  flex-direction: column;
}

.author-name {
  color: #1e293b;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.author-name:hover {
  color: #3b82f6;
}

.post-dates {
  font-size: 0.875rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.updated-date {
  font-style: italic;
}

.category-badge {
  padding: 0.5rem 1rem;
  border-radius: 50px;
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
}

.post-content {
  padding: 2rem;
}

.content-text {
  color: #334155;
  line-height: 1.8;
  font-size: 1.05rem;
}

.post-stats {
  margin-top: 2rem;
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.95rem;
}

.post-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f1f5f9;
}

.tags-label {
  color: #64748b;
  font-size: 0.95rem;
  margin-right: 1rem;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  padding: 0.35rem 0.75rem;
  background-color: #f1f5f9;
  border-radius: 4px;
  color: #334155;
  font-size: 0.875rem;
  text-decoration: none;
  transition: all 0.2s;
}

.tag:hover {
  background-color: #e0f2fe;
  color: #0369a1;
  transform: translateY(-2px);
}

.post-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

.vote-buttons {
  display: flex;
  gap: 0.75rem;
}

.vote-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background-color: white;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.vote-btn:hover {
  background-color: #f1f5f9;
}

.vote-btn.active {
  border-color: #3b82f6;
}

.vote-btn.upvote.active {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.vote-btn.downvote.active {
  background-color: #fee2e2;
  color: #b91c1c;
}

.vote-icon {
  font-size: 1.1rem;
}

.vote-count {
  font-weight: 600;
}

.share-buttons {
  display: flex;
  gap: 0.75rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background-color: white;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #f1f5f9;
}

.comments-section {
  padding: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1.5rem;
}

.comment-form {
  margin-bottom: 2.5rem;
}

.comment-input {
  width: 100%;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.comment-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.no-comments {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-style: italic;
  background-color: #f8fafc;
  border-radius: 8px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.comment-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  background-color: white;
}

.comment-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: #1e293b;
}

.comment-date {
  font-size: 0.875rem;
  color: #64748b;
}

.comment-content {
  color: #334155;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.comment-actions {
  display: flex;
  gap: 1rem;
}

.comment-action {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.comment-action:hover {
  color: #3b82f6;
  text-decoration: underline;
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

.author-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.author-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  width: 100%;
  margin: 1.5rem 0;
}

.author-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
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

.view-profile-btn {
  width: 100%;
  padding: 0.75rem 0;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #dbeafe;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  text-align: center;
  text-decoration: none;
  transition: all 0.2s;
}

.view-profile-btn:hover {
  background-color: #dbeafe;
}

/* Responsive design */
@media (max-width: 1200px) {
  .content-layout {
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 2rem;
  }
  
  .post-title {
    font-size: 2rem;
  }
}

@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    position: static;
    order: 1;
  }
  
  .post-container {
    order: 2;
  }
}

@media (max-width: 768px) {
  .post-detail-page {
    padding: 1rem 0 3rem;
  }
  
  .post-header {
    padding: 1.5rem 1.5rem 1rem;
  }
  
  .post-title {
    font-size: 1.75rem;
    margin-bottom: 1rem;
  }
  
  .post-content, .comments-section {
    padding: 1.5rem;
  }
  
  .post-actions {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .vote-buttons, .share-buttons {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .post-meta {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .breadcrumbs {
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
  }
  
  .section-title {
    font-size: 1.25rem;
  }
  
  .comment-item {
    padding: 1rem;
  }
}
</style> 