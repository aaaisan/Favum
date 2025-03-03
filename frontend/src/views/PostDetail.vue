<template>
  <div class="post-detail">
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="errorMessage" class="error">
      <i class="error-icon">!</i>
      <p>{{ errorMessage }}</p>
      <router-link to="/" class="btn-back">返回首页</router-link>
    </div>
    
    <template v-else-if="post">
      <div class="post-header">
        <h1>{{ post.title }}</h1>
        <div class="post-meta">
          <span>分类：{{ post.category?.name || '未分类' }}</span>
          <span>发布于：{{ formatDate(post.created_at) }}</span>
          <span v-if="post.updated_at !== post.created_at">
            更新于：{{ formatDate(post.updated_at) }}
          </span>
        </div>
      </div>
      
      <div class="post-content">
        {{ post.content }}
      </div>
      
      <div class="post-footer">
        <div class="post-tags" v-if="post.tags && post.tags.length > 0">
          <span class="tag" v-for="tag in post.tags" :key="tag.id">
            {{ tag.name }}
          </span>
        </div>
        
        <div class="post-actions">
          <button 
            class="btn-vote"
            :class="{ active: userVote === 'upvote' }"
            @click="handleVote('upvote')"
          >
            👍 赞 {{ post.vote_count || 0 }}
          </button>
          
          <button 
            class="btn-vote"
            :class="{ active: userVote === 'downvote' }"
            @click="handleVote('downvote')"
          >
            👎 踩
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePostDetail } from '../composables/usePostDetail'
import { formatDate } from '../utils/format'

const route = useRoute()
const postId = computed(() => Number(route.params.id))

// 使用帖子详情组合式函数
const {
  post,
  userVote,
  isLoading,
  errorMessage,
  fetchPost,
  handleVote
} = usePostDetail(postId.value)

onMounted(fetchPost)
</script>

<style scoped>
.post-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading, .error {
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

.btn-back {
  display: inline-block;
  margin-top: 20px;
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.btn-back:hover {
  background-color: #2980b9;
}

.post-header {
  margin-bottom: 30px;
}

.post-header h1 {
  margin: 0 0 15px;
  color: #2c3e50;
  font-size: 2em;
}

.post-meta {
  color: #666;
  font-size: 0.9em;
}

.post-meta span {
  margin-right: 15px;
}

.post-content {
  line-height: 1.6;
  color: #2c3e50;
  margin-bottom: 30px;
}

.post-footer {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.post-tags {
  margin-bottom: 20px;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  margin-right: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  font-size: 0.9em;
  color: #666;
}

.post-actions {
  display: flex;
  gap: 10px;
}

.btn-vote {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background-color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-vote:hover {
  background-color: #f8f9fa;
}

.btn-vote.active {
  background-color: #e3f2fd;
  border-color: #2196f3;
  color: #1976d2;
}
</style> 