<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="card-header">
          <h1 class="card-title">登录</h1>
          <p class="card-subtitle">欢迎回来，请登录您的账号</p>
        </div>
        
        <div class="card-body">
          <form class="auth-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label for="email">电子邮箱</label>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="请输入您的电子邮箱"
                required
                autocomplete="email"
              />
              <div v-if="emailError" class="error-text">{{ emailError }}</div>
            </div>
            
            <div class="form-group">
              <div class="password-label">
                <label for="password">密码</label>
                <router-link to="/forgot-password" class="forgot-password">
                  忘记密码?
                </router-link>
              </div>
              <div class="password-input">
                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入您的密码"
                  required
                  autocomplete="current-password"
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <div v-if="passwordError" class="error-text">{{ passwordError }}</div>
            </div>
            
            <div class="form-options">
              <label class="checkbox-label">
                <input type="checkbox" v-model="rememberMe" />
                <span>记住我</span>
              </label>
            </div>
            
            <button type="submit" class="submit-btn" :disabled="isLoading">
              <span v-if="isLoading" class="loader"></span>
              <span v-else>登录</span>
            </button>
          </form>
          
          <div class="divider">
            <span>或</span>
          </div>
          
          <div class="social-login">
            <button class="social-btn google">
              <span class="icon">G</span>
              <span>使用 Google 登录</span>
            </button>
            
            <button class="social-btn github">
              <span class="icon">GH</span>
              <span>使用 GitHub 登录</span>
            </button>
          </div>
        </div>
        
        <div class="card-footer">
          <p>还没有账号? <router-link to="/register" class="register-link">立即注册</router-link></p>
        </div>
      </div>
      
      <div class="brand-info">
        <div class="brand-logo">Forum</div>
        <h2 class="brand-title">加入我们的技术社区</h2>
        <p class="brand-description">
          连接开发者，分享知识，一起学习和成长。
        </p>
        <div class="testimonials">
          <div class="testimonial">
            <p class="quote">"这是我见过的最友好、最有帮助的技术社区！"</p>
            <div class="author">—— 张三，前端开发者</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表单数据
const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

// 错误信息
const emailError = ref('')
const passwordError = ref('')

// 加载状态
const isLoading = ref(false)

// 登录处理
const handleLogin = async () => {
  // 重置错误信息
  emailError.value = ''
  passwordError.value = ''
  
  // 表单验证
  let isValid = true
  
  if (!email.value) {
    emailError.value = '请输入电子邮箱'
    isValid = false
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    emailError.value = '请输入有效的电子邮箱'
    isValid = false
  }
  
  if (!password.value) {
    passwordError.value = '请输入密码'
    isValid = false
  }
  
  if (!isValid) return
  
  // 设置加载状态
  isLoading.value = true
  
  try {
    // 模拟API请求
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 实际应用中这里会调用登录API
    console.log('登录信息:', {
      email: email.value,
      password: '******',
      rememberMe: rememberMe.value
    })
    
    // 登录成功，跳转到首页
    router.push('/')
  } catch (error) {
    // 处理登录错误
    console.error('登录失败:', error)
    
    // 显示一般错误消息
    if (error instanceof Error) {
      passwordError.value = error.message
    } else {
      passwordError.value = '登录失败，请检查您的凭据'
    }
  } finally {
    // 重置加载状态
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  padding: 2rem 1rem;
}

.auth-container {
  width: 100%;
  max-width: 1200px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background-color: white;
}

.auth-card {
  padding: 3rem 2.5rem;
  display: flex;
  flex-direction: column;
}

.card-header {
  margin-bottom: 2.5rem;
}

.card-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 0.75rem;
}

.card-subtitle {
  color: #64748b;
  font-size: 1rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #334155;
  font-weight: 500;
  font-size: 0.95rem;
}

.password-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-password {
  color: #3b82f6;
  font-size: 0.85rem;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-password:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.form-group input {
  padding: 0.9rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  width: 100%;
  transition: all 0.2s;
}

.form-group input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.password-input {
  position: relative;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0;
}

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.form-options {
  display: flex;
  align-items: center;
  margin-top: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  color: #475569;
  font-size: 0.95rem;
}

.checkbox-label input {
  width: 1rem;
  height: 1rem;
}

.submit-btn {
  padding: 1rem;
  background-color: #3b82f6;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 3.25rem;
  margin-top: 1rem;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.loader {
  width: 1.5rem;
  height: 1.5rem;
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

.divider {
  display: flex;
  align-items: center;
  margin: 2rem 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.divider::before,
.divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background-color: #e2e8f0;
}

.divider span {
  margin: 0 1rem;
}

.social-login {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background-color: white;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.social-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.social-btn .icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.8rem;
}

.social-btn.google .icon {
  background-color: #db4437;
  color: white;
}

.social-btn.github .icon {
  background-color: #333;
  color: white;
}

.card-footer {
  margin-top: auto;
  padding-top: 2rem;
  text-align: center;
  color: #475569;
  font-size: 0.95rem;
}

.register-link {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.register-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.brand-info {
  background-color: #1e40af;
  background-image: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  color: white;
  padding: 4rem 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-logo {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 2rem;
  letter-spacing: -0.05em;
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1.5rem;
  line-height: 1.3;
}

.brand-description {
  font-size: 1.1rem;
  margin: 0 0 3rem;
  opacity: 0.9;
  line-height: 1.7;
}

.testimonials {
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  padding: 2rem;
  border-radius: 12px;
  margin-top: auto;
}

.quote {
  font-size: 1.1rem;
  font-style: italic;
  margin: 0 0 1rem;
  line-height: 1.6;
}

.author {
  font-size: 0.9rem;
  opacity: 0.8;
}

/* Responsive design */
@media (max-width: 1024px) {
  .auth-container {
    grid-template-columns: 1fr;
    max-width: 600px;
  }
  
  .brand-info {
    display: none;
  }
  
  .auth-card {
    padding: 2.5rem 2rem;
  }
}

@media (max-width: 640px) {
  .auth-card {
    padding: 2rem 1.5rem;
  }
  
  .card-title {
    font-size: 1.75rem;
  }
}
</style> 