<template>
  <div>
    <h1>帖子列表</h1>
    <ul>
      <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../services/api'

// 定义帖子类型
interface Post {
  id: number
  title: string
  // 如果有其他字段，也可以在这里添加
}

// 为posts指定类型
const posts = ref<Post[]>([])

onMounted(async () => {
  try {
    const response = await apiClient.get('/posts')
    posts.value = response.data
  } catch (error) {
    console.error('获取帖子列表失败:', error)
  }
})
</script>