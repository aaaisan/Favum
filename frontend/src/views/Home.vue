<template>
  <div>
    <h1>帖子列表</h1>
    <div v-if="isLoading" class="loading">加载中...</div>
    <div v-else-if="errorMessage" class="error">{{ errorMessage }}</div>
    <div v-else-if="posts.length === 0" class="empty">暂无帖子</div>
    <ul v-else>
      <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePostsStore } from '../stores/posts'

const postsStore = usePostsStore()

// 使用计算属性从store获取数据
const posts = computed(() => postsStore.postList?.posts || [])
const isLoading = computed(() => postsStore.isLoading)
const errorMessage = computed(() => postsStore.error)

onMounted(async () => {
  try {
    await postsStore.fetchPosts()
  } catch (error) {
    console.error('获取帖子列表失败:', error)
  }
})
</script>

<style scoped>
.loading, .error, .empty {
  padding: 20px;
  text-align: center;
}

.error {
  color: #e74c3c;
}
</style>