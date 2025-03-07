<template>
  <div class="create-post-container">
    <h1>发布新帖子</h1>
    <form @submit.prevent="handleSubmit" class="create-post-form">
      <div class="form-group">
        <label for="title">标题</label>
        <input 
          type="text" 
          id="title" 
          v-model="form.title" 
          :class="{ error: errors.title }"
        />
        <span class="error-message" v-if="errors.title">{{ errors.title }}</span>
      </div>
      
      <div class="form-group">
        <label for="category">分类</label>
        <select 
          id="category" 
          v-model="form.category_id" 
          :class="{ error: errors.category_id }"
        >
          <option value="0">请选择分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
        <span class="error-message" v-if="errors.category_id">{{ errors.category_id }}</span>
      </div>
      
      <div class="form-group">
        <label for="content">内容</label>
        <textarea 
          id="content" 
          v-model="form.content" 
          rows="10"
          :class="{ error: errors.content }"
        ></textarea>
        <span class="error-message" v-if="errors.content">{{ errors.content }}</span>
      </div>
      
      <div class="form-group">
        <label>标签</label>
        <div class="tags-container">
          <div 
            v-for="tag in selectedTags" 
            :key="tag"
            class="tag"
          >
            {{ tag }}
            <button type="button" class="remove-tag" @click="removeTag(tag)">×</button>
          </div>
          <input 
            type="text" 
            v-model="tagInput"
            @keydown.enter.prevent="addTag"
            placeholder="输入标签后按回车添加"
          />
        </div>
      </div>

      <div class="form-group">
        <label>验证码</label>
        <Captcha
          v-model="form.captcha_code"
          :error="errors.captcha_code"
          @refresh="handleCaptchaRefresh"
        />
      </div>

      <div class="error-message" v-if="errorMessage">{{ errorMessage }}</div>
      <div class="success-message" v-if="successMessage">{{ successMessage }}</div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '发布中...' : '发布帖子' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePostForm } from '../composables/usePostForm'
import { usePostStore } from '../stores/post'
import type { ForumCategory } from '../types/post'
import Captcha from '../components/Captcha.vue'

const router = useRouter()
const postStore = usePostStore()
const {
  form,
  errors,
  isSubmitting,
  successMessage,
  errorMessage,
  validate,
  resetForm,
  handleCaptchaRefresh
} = usePostForm()

const categories = ref<ForumCategory[]>([])
const tagInput = ref('')
const selectedTags = ref<string[]>([])

// 获取分类列表
const fetchCategories = async () => {
  try {
    categories.value = await postStore.fetchCategories()
  } catch (error) {
    errorMessage.value = '获取分类列表失败'
  }
}

// 添加标签
const addTag = () => {
  const tag = tagInput.value.trim()
  if (tag && !selectedTags.value.includes(tag)) {
    selectedTags.value.push(tag)
    form.tags = selectedTags.value
    tagInput.value = ''
  }
}

// 移除标签
const removeTag = (tag: string) => {
  selectedTags.value = selectedTags.value.filter(t => t !== tag)
  form.tags = selectedTags.value
}

const handleSubmit = async () => {
  if (!validate()) return

  try {
    isSubmitting.value = true
    const post = await postStore.createPost(form)
    successMessage.value = '发布成功！正在跳转到帖子详情页...'
    resetForm()
    setTimeout(() => {
      router.push(`/posts/${post.id}`)
    }, 2000)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '发布失败'
    if (error.response?.status === 400) {
      handleCaptchaRefresh()
    }
  } finally {
    isSubmitting.value = false
  }
}

// 初始化时获取分类列表
fetchCategories()
</script>

<style scoped>
.create-post-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}

.create-post-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #2c3e50;
}

input, textarea, select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

input.error, textarea.error, select.error {
  border-color: #e74c3c;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
}

.success-message {
  color: #2ecc71;
  font-size: 14px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #e1e8ed;
  border-radius: 4px;
  font-size: 14px;
}

.remove-tag {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 0 4px;
}

.remove-tag:hover {
  color: #e74c3c;
}

button[type="submit"] {
  padding: 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button[type="submit"]:hover:not(:disabled) {
  background-color: #2980b9;
}

button[type="submit"]:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}
</style> 