<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="card-header">
          <h1 class="card-title">注册账号</h1>
          <p class="card-subtitle">加入我们的技术社区，开始分享和学习</p>
        </div>
        
        <div class="card-body">
          <form class="auth-form" @submit.prevent="handleRegister">
            <div class="form-group">
              <label for="username">用户名</label>
              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="请输入您的用户名"
                required
                autocomplete="username"
              />
              <div v-if="usernameError" class="error-text">{{ usernameError }}</div>
            </div>
            
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
            
            <div class="form-row">
              <div class="form-group">
                <label for="password">密码</label>
                <div class="password-input">
                  <input
                    id="password"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="请输入密码"
                    required
                    autocomplete="new-password"
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
              
              <div class="form-group">
                <label for="confirm-password">确认密码</label>
                <div class="password-input">
                  <input
                    id="confirm-password"
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    placeholder="请确认密码"
                    required
                    autocomplete="new-password"
                  />
                  <button
                    type="button"
                    class="toggle-password"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    {{ showConfirmPassword ? '👁️' : '👁️‍🗨️' }}
                  </button>
                </div>
                <div v-if="confirmPasswordError" class="error-text">{{ confirmPasswordError }}</div>
              </div>
            </div>
            
            <div class="form-options">
              <label class="checkbox-label">
                <input type="checkbox" v-model="agreeTerms" required />
                <span>我已阅读并同意 <a href="#" class="terms-link">服务条款</a> 和 <a href="#" class="terms-link">隐私政策</a></span>
              </label>
            </div>
            
            <button type="submit" class="submit-btn" :disabled="isLoading || !agreeTerms">
              <span v-if="isLoading" class="loader"></span>
              <span v-else>创建账号</span>
            </button>
          </form>
          
          <div class="divider">
            <span>或</span>
          </div>
          
          <div class="social-login">
            <button class="social-btn google">
              <span class="icon">G</span>
              <span>使用 Google 注册</span>
            </button>
            
            <button class="social-btn github">
              <span class="icon">GH</span>
              <span>使用 GitHub 注册</span>
            </button>
          </div>
        </div>
        
        <div class="card-footer">
          <p>已有账号? <router-link to="/login" class="login-link">立即登录</router-link></p>
        </div>
      </div>
      
      <div class="brand-info">
        <div class="brand-logo">Forum</div>
        <h2 class="brand-title">成为社区的一员</h2>
        <p class="brand-description">
          注册成为会员，您将能够：
        </p>
        <ul class="benefits-list">
          <li class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">发布话题和回复评论</div>
          </li>
          <li class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">收藏喜欢的内容</div>
          </li>
          <li class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">与其他开发者交流与学习</div>
          </li>
          <li class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">获取专业技术资源和帮助</div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表单数据
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreeTerms = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// 错误信息
const usernameError = ref('')
const emailError = ref('')
const passwordError = ref('')
const confirmPasswordError = ref('')

// 加载状态
const isLoading = ref(false)

// 监听密码变化，清除确认密码错误
watch(password, () => {
  if (confirmPassword.value && password.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入的密码不一致'
  } else {
    confirmPasswordError.value = ''
  }
})

// 监听确认密码变化
watch(confirmPassword, () => {
  if (confirmPassword.value && password.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入的密码不一致'
  } else {
    confirmPasswordError.value = ''
  }
})

// 注册处理
const handleRegister = async () => {
  // 重置错误信息
  usernameError.value = ''
  emailError.value = ''
  passwordError.value = ''
  confirmPasswordError.value = ''
  
  // 表单验证
  let isValid = true
  
  if (!username.value) {
    usernameError.value = '请输入用户名'
    isValid = false
  } else if (username.value.length < 3) {
    usernameError.value = '用户名长度不能少于3个字符'
    isValid = false
  }
  
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
  } else if (password.value.length < 6) {
    passwordError.value = '密码长度不能少于6个字符'
    isValid = false
  }
  
  if (!confirmPassword.value) {
    confirmPasswordError.value = '请确认密码'
    isValid = false
  } else if (password.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入的密码不一致'
    isValid = false
  }
  
  if (!agreeTerms.value) {
    isValid = false
  }
  
  if (!isValid) return
  
  // 设置加载状态
  isLoading.value = true
  
  try {
    // 模拟API请求
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 实际应用中这里会调用注册API
    console.log('注册信息:', {
      username: username.value,
      email: email.value,
      password: '******'
    })
    
    // 注册成功，跳转到登录页
    router.push('/login')
  } catch (error) {
    // 处理注册错误
    console.error('注册失败:', error)
    
    // 显示错误消息
    if (error instanceof Error) {
      if (error.message.includes('email')) {
        emailError.value = error.message
      } else if (error.message.includes('username')) {
        usernameError.value = error.message
      } else {
        emailError.value = error.message
      }
    } else {
      emailError.value = '注册失败，请稍后再试'
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
  gap: 1.25rem;
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
  gap: 1rem;
}

.form-group label {
  color: #334155;
  font-weight: 500;
  font-size: 0.95rem;
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
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.5;
}

.checkbox-label input {
  width: 1rem;
  height: 1rem;
  margin-top: 0.25rem;
}

.terms-link {
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.2s;
}

.terms-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
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

.login-link {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s;
}

.login-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.brand-info {
  background-color: #064e3b;
  background-image: linear-gradient(135deg, #064e3b 0%, #10b981 100%);
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
  margin: 0 0 2rem;
  opacity: 0.9;
  line-height: 1.7;
}

.benefits-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.benefit-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.benefit-icon {
  width: 2rem;
  height: 2rem;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.benefit-text {
  font-size: 1.05rem;
  line-height: 1.6;
  padding-top: 0.25rem;
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
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style> 
