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
    
    <template v-else-if="user">
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
            <div class="info-label">个人简介</div>
            <div class="info-value">{{ user.bio || '暂无简介' }}</div>
          </div>
        </div>
      </div>
      
      <!-- 用户统计标签页 -->
      <div v-else-if="activeTab === 'stats'" class="profile-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{{ userStats?.post_count || 0 }}</div>
            <div class="stat-label">发布帖子</div>
            <button @click="viewUserPosts" class="btn-view">查看帖子</button>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ userStats?.comment_count || 0 }}</div>
            <div class="stat-label">发表评论</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ userStats?.reputation || 0 }}</div>
            <div class="stat-label">声望</div>
          </div>
        </div>
      </div>
      
      <!-- 编辑资料标签页 -->
      <div v-else-if="activeTab === 'edit'" class="profile-section">
        <form @submit.prevent="handleSubmit" class="edit-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              :class="{ error: errors.username }"
            />
            <span class="error-message" v-if="errors.username">{{ errors.username }}</span>
          </div>
          
          <div class="form-group">
            <label for="email">邮箱</label>
            <input 
              type="email" 
              id="email" 
              v-model="form.email" 
              :class="{ error: errors.email }"
            />
            <span class="error-message" v-if="errors.email">{{ errors.email }}</span>
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
              :class="{ error: errors.password }"
              autocomplete="new-password"
            />
            <span class="error-message" v-if="errors.password">{{ errors.password }}</span>
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="form.confirmPassword"
              :class="{ error: errors.confirmPassword }"
              :disabled="!form.password"
            />
            <span class="error-message" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
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
          
          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
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
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useUserProfileForm } from '../composables/useUserProfileForm'
import { formatDate, getInitials } from '../utils/format'
import { formatRole, getRoleBadgeClass } from '../utils/roles'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 获取用户ID
const userId = computed(() => Number(route.params.userId))

// 从store获取数据
const user = computed(() => userStore.currentUser)
const userStats = computed(() => userStore.userStats)
const isLoading = computed(() => userStore.isLoading)
const errorMessage = computed(() => userStore.error)

// 使用用户资料表单组合式函数
const {
  form,
  errors,
  isSubmitting,
  successMessage,
  resetForm,
  validate
} = useUserProfileForm(user.value)

// 当前激活的标签页
const activeTab = ref('info')

// 检查是否有权限编辑
const canEdit = computed(() => {
  // TODO: 根据实际权限逻辑判断
  return true
})

// 获取用户资料
const fetchUserProfile = async () => {
  try {
    await userStore.fetchUserProfile(userId.value)
    await userStore.fetchUserStats(userId.value)
  } catch (error) {
    console.error('获取用户资料失败:', error)
  }
}

// 处理表单提交
const handleSubmit = async () => {
  if (!validate()) return
  if (!user.value) return

  try {
    isSubmitting.value = true
    await userStore.updateUserProfile(user.value.id, {
      username: form.value.username,
      email: form.value.email,
      bio: form.value.bio || null,
      password: form.value.password || undefined
    })
    successMessage.value = '资料更新成功'
    resetForm()
    activeTab.value = 'info'
  } catch (error: any) {
    userStore.error = error.response?.data?.detail || '更新资料失败'
  } finally {
    isSubmitting.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  resetForm()
  activeTab.value = 'info'
}

// 查看用户帖子
const viewUserPosts = () => {
  router.push(`/users/${userId.value}/posts`)
}

// 监听用户ID变化，重新获取数据
watch(() => userId.value, fetchUserProfile, { immediate: true })
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading, .error-container {
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

.btn-retry {
  margin-top: 20px;
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.avatar-container {
  width: 80px;
  height: 80px;
}

.avatar {
  width: 100%;
  height: 100%;
  background-color: #3498db;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
}

.profile-title {
  flex: 1;
}

.profile-title h1 {
  margin: 0 0 8px;
  color: #2c3e50;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.role-badge.admin {
  background-color: #e74c3c;
  color: white;
}

.role-badge.moderator {
  background-color: #f39c12;
  color: white;
}

.role-badge.user {
  background-color: #95a5a6;
  color: white;
}

.profile-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.profile-tabs button {
  padding: 8px 16px;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  font-size: 16px;
  border-radius: 4px;
}

.profile-tabs button.active {
  background-color: #3498db;
  color: white;
}

.profile-section {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
}

.info-grid {
  display: grid;
  gap: 20px;
}

.info-item {
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.info-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 5px;
}

.info-value {
  color: #2c3e50;
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 8px;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
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

.edit-form {
  max-width: 500px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
}

input, textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

input.error {
  border-color: #e74c3c;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  margin-top: 4px;
}

.success-message {
  color: #2ecc71;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-submit {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  padding: 10px 20px;
  background-color: #95a5a6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-submit:hover, .btn-cancel:hover {
  opacity: 0.9;
}

.btn-submit:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}
</style>
