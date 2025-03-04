<template>
  <div class="settings-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">账号设置</h1>
        <p class="page-subtitle">管理您的个人信息、隐私和安全设置</p>
      </div>
      
      <div class="settings-layout">
        <div class="settings-sidebar">
          <div class="user-info">
            <div class="user-avatar">
              <span v-if="!currentUser.avatar">{{ getUserInitials(currentUser.name) }}</span>
              <img v-else :src="currentUser.avatar" :alt="currentUser.name" />
            </div>
            <div class="user-name">{{ currentUser.name }}</div>
            <div class="user-email">{{ currentUser.email }}</div>
          </div>
          
          <nav class="settings-nav">
            <router-link to="/settings/profile" class="nav-item" :class="{ active: currentTab === 'profile' }">
              <span class="nav-icon">👤</span>
              <span class="nav-text">个人资料</span>
            </router-link>
            
            <router-link to="/settings/account" class="nav-item" :class="{ active: currentTab === 'account' }">
              <span class="nav-icon">🔐</span>
              <span class="nav-text">账号安全</span>
            </router-link>
            
            <router-link to="/settings/notifications" class="nav-item" :class="{ active: currentTab === 'notifications' }">
              <span class="nav-icon">🔔</span>
              <span class="nav-text">通知设置</span>
            </router-link>
            
            <router-link to="/settings/privacy" class="nav-item" :class="{ active: currentTab === 'privacy' }">
              <span class="nav-icon">🛡️</span>
              <span class="nav-text">隐私设置</span>
            </router-link>
            
            <router-link to="/settings/appearance" class="nav-item" :class="{ active: currentTab === 'appearance' }">
              <span class="nav-icon">🎨</span>
              <span class="nav-text">界面设置</span>
            </router-link>
          </nav>
          
          <div class="sidebar-footer">
            <button class="logout-btn" @click="logout">
              <span class="logout-icon">🚪</span>
              <span>退出登录</span>
            </button>
          </div>
        </div>
        
        <div class="settings-content">
          <!-- 个人资料设置 -->
          <div v-if="currentTab === 'profile'" class="settings-section">
            <div class="section-header">
              <h2 class="section-title">个人资料</h2>
              <p class="section-subtitle">更新您的个人信息和公开资料</p>
            </div>
            
            <form class="settings-form" @submit.prevent="saveProfile">
              <div class="form-group">
                <label for="avatar">头像</label>
                <div class="avatar-upload">
                  <div class="current-avatar">
                    <span v-if="!profileForm.avatar">{{ getUserInitials(profileForm.name) }}</span>
                    <img v-else :src="profileForm.avatar" :alt="profileForm.name" />
                  </div>
                  
                  <div class="upload-actions">
                    <button type="button" class="upload-btn">上传新头像</button>
                    <button 
                      v-if="profileForm.avatar" 
                      type="button" 
                      class="remove-btn"
                      @click="removeAvatar"
                    >
                      移除头像
                    </button>
                  </div>
                </div>
                <div class="form-hint">推荐上传正方形图片，最大支持2MB</div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="name">用户名 <span class="required">*</span></label>
                  <input
                    id="name"
                    v-model="profileForm.name"
                    type="text"
                    placeholder="输入您的用户名"
                    required
                  />
                  <div v-if="formErrors.name" class="error-text">{{ formErrors.name }}</div>
                </div>
                
                <div class="form-group">
                  <label for="display-name">显示名称</label>
                  <input
                    id="display-name"
                    v-model="profileForm.displayName"
                    type="text"
                    placeholder="输入您的显示名称"
                  />
                  <div class="form-hint">如未设置，将使用用户名</div>
                </div>
              </div>
              
              <div class="form-group">
                <label for="bio">个人简介</label>
                <textarea
                  id="bio"
                  v-model="profileForm.bio"
                  placeholder="介绍一下自己..."
                  rows="4"
                ></textarea>
                <div class="char-counter" :class="{ 'warning': profileForm.bio.length > 200 }">
                  {{ profileForm.bio.length }}/300
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="location">所在地</label>
                  <input
                    id="location"
                    v-model="profileForm.location"
                    type="text"
                    placeholder="输入您的所在地"
                  />
                </div>
                
                <div class="form-group">
                  <label for="website">个人网站</label>
                  <input
                    id="website"
                    v-model="profileForm.website"
                    type="url"
                    placeholder="https://example.com"
                  />
                </div>
              </div>
              
              <div class="form-group">
                <label>社交账号</label>
                <div class="social-links">
                  <div class="social-link">
                    <div class="social-icon github">GH</div>
                    <input
                      v-model="profileForm.socials.github"
                      type="text"
                      placeholder="GitHub用户名"
                    />
                  </div>
                  
                  <div class="social-link">
                    <div class="social-icon twitter">TW</div>
                    <input
                      v-model="profileForm.socials.twitter"
                      type="text"
                      placeholder="Twitter用户名"
                    />
                  </div>
                  
                  <div class="social-link">
                    <div class="social-icon linkedin">LI</div>
                    <input
                      v-model="profileForm.socials.linkedin"
                      type="text"
                      placeholder="LinkedIn用户名"
                    />
                  </div>
                </div>
              </div>
              
              <div class="form-actions">
                <button type="button" class="cancel-btn" @click="resetProfile">取消</button>
                <button 
                  type="submit" 
                  class="save-btn" 
                  :disabled="isSaving"
                >
                  <span v-if="isSaving" class="loader"></span>
                  <span v-else>保存更改</span>
                </button>
              </div>
            </form>
          </div>
          
          <!-- 其他设置标签页 -->
          <div v-else class="settings-section">
            <div class="coming-soon">
              <div class="coming-soon-icon">🚧</div>
              <h3>功能开发中</h3>
              <p>{{ getTabMessage() }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 当前用户数据
const currentUser = reactive({
  id: 1,
  name: '张三',
  email: 'zhangsan@example.com',
  avatar: ''
})

// 个人资料表单
const profileForm = reactive({
  name: '张三',
  displayName: '',
  bio: '前端开发工程师，热爱技术分享，喜欢帮助他人解决问题。擅长 Vue.js, React, TypeScript。业余爱好包括阅读、烹饪和徒步旅行。',
  avatar: '',
  location: '北京',
  website: 'https://example.com',
  socials: {
    github: 'zhangsan',
    twitter: 'zhangsan',
    linkedin: 'zhangsan'
  }
})

// 表单错误
const formErrors = reactive({
  name: '',
  bio: ''
})

// 保存状态
const isSaving = ref(false)

// 获取当前标签页
const currentTab = computed(() => {
  const path = route.path
  if (path.includes('/settings/account')) return 'account'
  if (path.includes('/settings/notifications')) return 'notifications'
  if (path.includes('/settings/privacy')) return 'privacy'
  if (path.includes('/settings/appearance')) return 'appearance'
  return 'profile'
})

// 获取用户名缩写
const getUserInitials = (name: string) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

// 获取标签页消息
const getTabMessage = () => {
  switch (currentTab.value) {
    case 'account': return '账号安全设置功能即将上线，敬请期待'
    case 'notifications': return '通知设置功能即将上线，敬请期待'
    case 'privacy': return '隐私设置功能即将上线，敬请期待'
    case 'appearance': return '界面设置功能即将上线，敬请期待'
    default: return '该功能正在开发中，敬请期待'
  }
}

// 移除头像
const removeAvatar = () => {
  profileForm.avatar = ''
}

// 重置个人资料表单
const resetProfile = () => {
  profileForm.name = currentUser.name
  profileForm.displayName = ''
  profileForm.bio = '前端开发工程师，热爱技术分享，喜欢帮助他人解决问题。擅长 Vue.js, React, TypeScript。业余爱好包括阅读、烹饪和徒步旅行。'
  profileForm.avatar = currentUser.avatar
  profileForm.location = '北京'
  profileForm.website = 'https://example.com'
  profileForm.socials.github = 'zhangsan'
  profileForm.socials.twitter = 'zhangsan'
  profileForm.socials.linkedin = 'zhangsan'
  
  // 重置错误
  formErrors.name = ''
  formErrors.bio = ''
}

// 保存个人资料
const saveProfile = async () => {
  // 重置错误
  formErrors.name = ''
  formErrors.bio = ''
  
  // 表单验证
  let isValid = true
  
  if (!profileForm.name.trim()) {
    formErrors.name = '请输入用户名'
    isValid = false
  } else if (profileForm.name.length < 3) {
    formErrors.name = '用户名长度不能少于3个字符'
    isValid = false
  }
  
  if (profileForm.bio.length > 300) {
    formErrors.bio = '个人简介不能超过300个字符'
    isValid = false
  }
  
  if (!isValid) return
  
  // 设置保存状态
  isSaving.value = true
  
  try {
    // 模拟API请求
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 实际应用中这里会调用API
    console.log('保存个人资料:', profileForm)
    
    // 更新当前用户数据
    currentUser.name = profileForm.name
    currentUser.avatar = profileForm.avatar
    
    // 显示成功消息
    alert('个人资料已更新')
  } catch (error) {
    // 处理保存错误
    console.error('保存失败:', error)
    
    // 显示错误消息
    if (error instanceof Error) {
      formErrors.name = error.message
    } else {
      formErrors.name = '保存失败，请稍后再试'
    }
  } finally {
    // 重置保存状态
    isSaving.value = false
  }
}

// 退出登录
const logout = () => {
  if (confirm('确定要退出登录吗？')) {
    // 实际应用中这里会调用登出API
    console.log('退出登录')
    
    // 跳转到登录页
    router.push('/login')
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 实际应用中这里会加载用户数据
  console.log('加载用户设置')
  
  // 设置初始表单数据
  resetProfile()
})
</script>

<style scoped>
.settings-page {
  width: 100%;
  background-color: #f8fafc;
  min-height: 100vh;
  padding: 2rem 0 4rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.page-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  color: #64748b;
}

.settings-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2.5rem;
  align-items: start;
}

.settings-sidebar {
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 2rem;
}

.user-info {
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid #f1f5f9;
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 600;
  margin: 0 auto 1rem;
  overflow: hidden;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.875rem;
  color: #64748b;
}

.settings-nav {
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  color: #475569;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background-color: #f8fafc;
}

.nav-item.active {
  background-color: #eff6ff;
  color: #1d4ed8;
  font-weight: 500;
}

.nav-icon {
  font-size: 1.25rem;
  width: 1.5rem;
  display: flex;
  justify-content: center;
}

.sidebar-footer {
  padding: 1.5rem;
  border-top: 1px solid #f1f5f9;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem;
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fee2e2;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background-color: #fee2e2;
}

.logout-icon {
  font-size: 1.25rem;
}

.settings-content {
  width: 100%;
}

.settings-section {
  background-color: white;
  border-radius: 12px;
  padding: 2rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem;
}

.section-subtitle {
  color: #64748b;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.required {
  color: #ef4444;
}

.form-group label {
  font-weight: 600;
  color: #334155;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.form-hint {
  font-size: 0.825rem;
  color: #94a3b8;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.current-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background-color: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 600;
  overflow: hidden;
}

.current-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.upload-btn, .remove-btn {
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn {
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #dbeafe;
}

.upload-btn:hover {
  background-color: #dbeafe;
}

.remove-btn {
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fee2e2;
}

.remove-btn:hover {
  background-color: #fee2e2;
}

.char-counter {
  text-align: right;
  font-size: 0.825rem;
  color: #94a3b8;
}

.char-counter.warning {
  color: #f59e0b;
}

.error-text {
  color: #ef4444;
  font-size: 0.875rem;
}

.social-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.social-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.social-icon.github {
  background-color: #333;
}

.social-icon.twitter {
  background-color: #1da1f2;
}

.social-icon.linkedin {
  background-color: #0077b5;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
}

.cancel-btn, .save-btn {
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background-color: white;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.cancel-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.save-btn {
  background-color: #3b82f6;
  color: white;
  border: none;
  min-width: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.save-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.save-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.loader {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  text-align: center;
}

.coming-soon-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
}

.coming-soon h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin: 0 0 1rem;
}

.coming-soon p {
  color: #64748b;
  max-width: 500px;
  margin: 0;
}

/* Responsive design */
@media (max-width: 1024px) {
  .settings-layout {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .settings-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .settings-section {
    padding: 1.5rem;
  }
  
  .avatar-upload {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .cancel-btn, .save-btn {
    width: 100%;
  }
}
</style> 