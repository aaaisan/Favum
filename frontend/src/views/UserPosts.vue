<template>
  <div class="user-posts-container">
    <h1>用户帖子</h1>
    
    <div class="user-info" v-if="username">
      <h2>{{ username }}发布的帖子</h2>
    </div>
    
    <div v-if="isLoading" class="loading">
      加载中...
    </div>
    
    <div v-else-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
    
    <div v-else-if="posts.length === 0" class="empty-message">
      该用户还没有发布任何帖子
    </div>
    
    <div v-else class="posts-list">
      <div v-for="post in posts" :key="post.id" class="post-card">
        <div class="post-header">
          <h3 class="post-title">{{ post.title }}</h3>
          <span class="post-date">{{ formatDate(post.created_at) }}</span>
        </div>
        
        <div class="post-content" v-if="post.content">
          {{ truncateContent(post.content) }}
        </div>
        
        <div class="post-footer">
          <div class="post-stats">
            <span class="stat">
              <i class="icon-comment"></i> {{ post.comment_count || 0 }} 评论
            </span>
            <span class="stat">
              <i class="icon-like"></i> {{ post.like_count || 0 }} 点赞
            </span>
            <span class="stat">
              <i class="icon-view"></i> {{ post.view_count || 0 }} 浏览
            </span>
          </div>
          
          <button @click="viewPost(post.id)" class="btn-view">查看详情</button>
        </div>
      </div>
    </div>
    
    <div class="pagination" v-if="posts.length > 0">
      <button 
        :disabled="page === 1" 
        @click="changePage(page - 1)" 
        class="btn-pagination"
      >
        上一页
      </button>
      <span>第 {{ page }} 页</span>
      <button 
        :disabled="posts.length < pageSize" 
        @click="changePage(page + 1)" 
        class="btn-pagination"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePostsStore } from '../stores/posts'
import { useUsersStore } from '../stores/users'
import { formatDate, truncateText } from '../utils/format'

const router = useRouter()
const route = useRoute()
const postsStore = usePostsStore()
const usersStore = useUsersStore()

const page = ref(1)
const pageSize = 10

// 获取路由参数中的用户ID
const userId = computed(() => {
  return Number(route.params.userId)
})

// 从store获取数据的计算属性
const posts = computed(() => {
  return postsStore.userPosts?.posts || []
})

const isLoading = computed(() => postsStore.isLoading || usersStore.isLoading)
const errorMessage = computed(() => postsStore.error || usersStore.error)
const username = computed(() => usersStore.currentUser?.username || '')

// 截断内容
const truncateContent = (content: string, maxLength = 150) => {
  return truncateText(content, maxLength)
}

// 查看帖子详情
const viewPost = (postId: number) => {
  router.push(`/posts/${postId}`)
}

// 更改页码
const changePage = (newPage: number) => {
  page.value = newPage
  fetchData()
}

// 获取数据
const fetchData = async () => {
  try {
    // 获取用户信息
    await usersStore.fetchUserById(userId.value)
    
    // 获取用户帖子
    await postsStore.fetchUserPosts(userId.value, page.value, pageSize)
  } catch (error) {
    console.error('获取数据失败', error)
  }
}

// 监听路由参数变化
watch(() => route.params.userId, () => {
  page.value = 1 // 重置页码
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.user-posts-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.user-info {
  margin-bottom: 20px;
}

.loading, .error-message, .empty-message {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error-message {
  color: #e74c3c;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.post-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.post-title {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.post-date {
  font-size: 14px;
  color: #777;
}

.post-content {
  margin-bottom: 16px;
  color: #555;
  line-height: 1.5;
  font-size: 14px;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-stats {
  display: flex;
  gap: 16px;
}

.stat {
  font-size: 14px;
  color: #666;
}

button {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn-view {
  background-color: #3498db;
  color: white;
}

.btn-pagination {
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  color: #333;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}
</style>
