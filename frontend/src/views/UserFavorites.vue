<template>
  <div class="user-favorites">
    <h1>我的收藏</h1>
    <div v-if="isLoading" class="loading">
      加载中...
    </div>
    <div v-else-if="errorMessage" class="error">
      {{ errorMessage }}
    </div>
    <div v-else-if="favorites.length === 0" class="empty">
      暂无收藏内容
    </div>
    <ul v-else class="favorites-list">
      <li v-for="post in favorites" :key="post.id" class="favorite-item">
        <div class="post-title">{{ post.title }}</div>
        <div class="post-info">
          <span>发布于: {{ formatDate(post.created_at) }}</span>
        </div>
        <div class="post-actions">
          <button @click="viewPost(post.id)" class="btn-view">查看</button>
          <button @click="removeFavorite(post.id)" class="btn-remove">取消收藏</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePostsStore } from '../stores/posts'
import { formatDate } from '../utils/format'
import type { Post } from '../types'

const router = useRouter()
const route = useRoute()
const postsStore = usePostsStore()

// 获取当前用户ID，如果是查看其他用户的收藏，则从路由中获取
const userId = computed(() => {
  if (route.params.userId) {
    return Number(route.params.userId)
  }
  return 0 // 当前登录用户
})

// 从store获取数据的计算属性
const favorites = computed<Post[]>(() => {
  return postsStore.favoritesList?.posts || []
})

const isLoading = computed(() => postsStore.isLoading)
const errorMessage = computed(() => postsStore.error)

// 查看帖子详情
const viewPost = (postId: number) => {
  router.push(`/posts/${postId}`)
}

// 取消收藏
const removeFavorite = async (postId: number) => {
  try {
    await postsStore.unfavoritePost(postId)
    // 刷新收藏列表
    fetchFavorites()
  } catch (error) {
    console.error('取消收藏失败', error)
  }
}

// 获取收藏列表
const fetchFavorites = async () => {
  try {
    await postsStore.fetchUserFavorites(userId.value)
  } catch (error) {
    console.error('获取收藏列表失败', error)
  }
}

onMounted(fetchFavorites)
</script>

<style scoped>
.user-favorites {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading, .error, .empty {
  text-align: center;
  margin: 40px 0;
  color: #666;
}

.error {
  color: #e74c3c;
}

.favorites-list {
  list-style: none;
  padding: 0;
}

.favorite-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: box-shadow 0.3s;
}

.favorite-item:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.post-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}

.post-info {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.post-actions {
  display: flex;
  gap: 10px;
}

button {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}

.btn-view {
  background-color: #3498db;
  color: white;
}

.btn-remove {
  background-color: #e74c3c;
  color: white;
}

button:hover {
  opacity: 0.9;
}
</style>