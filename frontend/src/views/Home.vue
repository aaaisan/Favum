<template>
  <div class="home">
    <h1>帖子列表</h1>
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else-if="errorMessage" class="error">
      <i class="error-icon">!</i>
      <p>{{ errorMessage }}</p>
    </div>
    <div v-else-if="posts.length === 0" class="empty">
      <p>暂无帖子</p>
    </div>
    <div v-else class="posts-container">
      <ul class="posts-list">
        <li v-for="post in posts" :key="post.id" class="post-item">
          <h3>{{ post.title }}</h3>
          <p class="post-meta">
            <span>作者: {{ post.author_name }}</span>
            <span>发布于: {{ formatDate(post.created_at) }}</span>
          </p>
        </li>
      </ul>
      
      <div class="pagination">
        <button 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
          class="btn-pagination"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
        </span>
        <button 
          :disabled="currentPage >= totalPages" 
          @click="changePage(currentPage + 1)"
          class="btn-pagination"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { usePostsStore } from '../stores/posts'
import { formatDate } from '../utils/format'

const postsStore = usePostsStore()
const currentPage = ref(1)
const pageSize = ref(10)

// 使用计算属性从store获取数据
const posts = computed(() => postsStore.postList?.posts || [])
const totalPages = computed(() => postsStore.totalPages)
const isLoading = computed(() => postsStore.isLoading)
const errorMessage = computed(() => postsStore.error)

// 切换页码
const changePage = async (page: number) => {
  currentPage.value = page
  await fetchPosts()
}

// 获取帖子列表
const fetchPosts = async () => {
  try {
    await postsStore.fetchPosts(currentPage.value, pageSize.value)
  } catch (error) {
    console.error('获取帖子列表失败:', error)
  }
}

// 组件挂载时获取帖子列表
onMounted(fetchPosts)
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  color: #666;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3498db;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  display: inline-block;
  width: 36px;
  height: 36px;
  line-height: 36px;
  text-align: center;
  background-color: #e74c3c;
  color: white;
  border-radius: 50%;
  font-style: normal;
  font-weight: bold;
  font-size: 20px;
  margin-bottom: 10px;
}

.posts-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.post-item {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.post-item h3 {
  margin: 0 0 10px;
  color: #2c3e50;
}

.post-meta {
  font-size: 14px;
  color: #666;
}

.post-meta span {
  margin-right: 15px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 20px 0;
}

.btn-pagination {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background-color: #fff;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-pagination:hover:not(:disabled) {
  background-color: #f8f9fa;
}

.btn-pagination:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}
</style>