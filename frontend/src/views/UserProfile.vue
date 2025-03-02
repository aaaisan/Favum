<template>
  <div class="profile-container">
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>加载用户资料中...</p>
    </div>
    
    <div v-else-if="errorMessage" class="error-container">
      <div class="error-icon">!</div>
      <h2>出错了</h2>
      <p>{{ errorMessage }}</p>
      <button @click="fetchUserProfile" class="btn-retry">重试</button>
    </div>
    
    <template v-else>
      <div class="profile-header">
        <div class="avatar-container">
          <div class="avatar">{{ getInitials(user.username) }}</div>
        </div>
        <div class="profile-title">
          <h1>{{ user.username }}</h1>
          <div class="role-badge" :class="getRoleBadgeClass(user.role)">
            {{ formatRole(user.role) }}
          </div>
        </div>
      </div>
      
      <div class="profile-tabs">
        <button 
          @click="activeTab = 'info'" 
          :class="{ active: activeTab === 'info' }"
        >
          基本信息
        </button>
        <button 
          @click="activeTab = 'stats'" 
          :class="{ active: activeTab === 'stats' }"
        >
          用户统计
        </button>
        <button 
          @click="activeTab = 'edit'" 
          :class="{ active: activeTab === 'edit' }"
          v-if="canEdit"
        >
          编辑资料
        </button>
      </div>
      
      <!-- 基本信息标签页 -->
      <div v-if="activeTab === 'info'" class="profile-section">
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">用户名</div>
            <div class="info-value">{{ user.username }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">邮箱</div>
            <div class="info-value">{{ user.email }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">注册时间</div>
            <div class="info-value">{{ formatDate(user.created_at) }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">上次活跃</div>
            <div class="info-value">{{ user.last_login ? formatDate(user.last_login) : '暂无数据' }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">个人简介</div>
            <div class="info-value">{{ user.bio || '暂无简介' }}</div>
          </div>
        </div>
      </div>
      
      <!-- 用户统计标签页 -->
      <div v-else-if="activeTab === 'stats'" class="profile-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{{ userStats.postCount || 0 }}</div>
            <div class="stat-label">发布帖子</div>
            <button @click="viewUserPosts" class="btn-view">查看帖子</button>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ userStats.commentCount || 0 }}</div>
            <div class="stat-label">发表评论</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ userStats.favoriteCount || 0 }}</div>
            <div class="stat-label">收藏帖子</div>
            <button @click="viewUserFavorites" class="btn-view">查看收藏</button>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ userStats.likeCount || 0 }}</div>
            <div class="stat-label">获得点赞</div>
          </div>
        </div>
      </div>
      
      <!-- 编辑资料标签页 -->
      <div v-else-if="activeTab === 'edit'" class="profile-section">
        <form @submit.prevent="updateProfile" class="edit-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              required
            />
            <div v-if="errors.username" class="form-error">
              {{ errors.username }}
            </div>
          </div>
          
          <div class="form-group">
            <label for="email">邮箱</label>
            <input 
              type="email" 
              id="email" 
              v-model="form.email" 
              required
            />
            <div v-if="errors.email" class="form-error">
              {{ errors.email }}
            </div>
          </div>
          
          <div class="form-group">
            <label for="bio">个人简介</label>
            <textarea 
              id="bio" 
              v-model="form.bio" 
              rows="4"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="password">新密码 (留空则不修改)</label>
            <input 
              type="password" 
              id="password" 
              v-model="form.password"
              autocomplete="new-password"
            />
            <div v-if="errors.password" class="form-error">
              {{ errors.password }}
            </div>
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="form.confirmPassword"
              :disabled="!form.password"
            />
            <div v-if="errors.confirmPassword" class="form-error">
              {{ errors.confirmPassword }}
            </div>
          </div>
          
          <div class="form-actions">
            <button 
              type="submit" 
              class="btn-submit" 
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? '保存中...' : '保存修改' }}
            </button>
            <button 
              type="button" 
              class="btn-cancel" 
              @click="cancelEdit"
            >
              取消
            </button>
          </div>
          
          <div v-if="updateSuccess" class="success-message">
            资料更新成功！
          </div>
          
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </form>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserProfile } from '../composables/useUserProfile'
import { formatDate, getInitials } from '../utils/format'
import { formatRole, getRoleBadgeClass } from '../utils/roles'
import type { User, UserStats } from '../types'

const route = useRoute()
const router = useRouter()

// 获取用户ID
const userId = computed(() => {
  return Number(route.params.userId)
})

// 使用用户个人资料组合式函数
const {
  user,
  userStats,
  isLoading,
  errorMessage,
  isSubmitting,
  updateSuccess,
  activeTab,
  form,
  errors,
  fetchUserProfile,
  updateProfile,
  cancelEdit
} = useUserProfile(userId)

// 检查是否有权限编辑
const canEdit = computed(() => {
  // 如果是当前用户或管理员
  return true // 这里应该根据实际权限逻辑来判断
})

// 查看用户帖子
const viewUserPosts = () => {
  router.push(`/users/${userId.value}/posts`)
}

// 查看用户收藏
const viewUserFavorites = () => {
  router.push(`/users/${userId.value}/favorites`)
}

// 监听用户ID变化，重新获取数据
watch(() => userId.value, () => {
  fetchUserProfile()
})

onMounted(() => {
  fetchUserProfile()
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-left-color: #3498db;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container {
  text-align: center;
  padding: 40px 0;
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background-color: #e74c3c;
  color: white;
  border-radius: 50%;
  font-size: 30px;
  font-weight: bold;
  margin: 0 auto 20px;
}

.profile-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.avatar-container {
  margin-right: 20px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
}

.profile-title {
  display: flex;
  flex-direction: column;
}

.profile-title h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  width: fit-content;
}

.role-user {
  background-color: #f1c40f;
  color: #000;
}

.role-admin {
  background-color: #e74c3c;
  color: white;
}

.role-super_admin {
  background-color: #9b59b6;
  color: white;
}

.role-moderator {
  background-color: #27ae60;
  color: white;
}

.profile-tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.profile-tabs button {
  padding: 10px 16px;
  background-color: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.profile-tabs button.active {
  border-bottom: 2px solid #3498db;
  color: #3498db;
}

.profile-section {
  padding: 20px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.info-item {
  margin-bottom: 16px;
}

.info-label {
  font-weight: bold;
  margin-bottom: 4px;
  color: #666;
  font-size: 14px;
}

.info-value {
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #3498db;
  margin-bottom: 8px;
}

.stat-label {
  color: #666;
  margin-bottom: 12px;
}

.edit-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.form-group textarea {
  resize: vertical;
}

.form-error {
  color: #e74c3c;
  font-size: 14px;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.btn-submit {
  padding: 10px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn-cancel {
  padding: 10px 16px;
  background-color: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn-view {
  padding: 6px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-retry {
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 16px;
}

.success-message {
  padding: 10px;
  background-color: #d4edda;
  color: #155724;
  border-radius: 4px;
  margin-top: 16px;
}

.error-message {
  padding: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  margin-top: 16px;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}
</style>
