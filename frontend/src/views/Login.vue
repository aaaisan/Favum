<template>
  <div class="login-container">
    <h1>用户登录</h1>
    <form @submit.prevent="login" class="login-form">
      <div class="form-group">
        <label for="username">用户名或邮箱</label>
        <input 
          type="text" 
          id="username" 
          v-model="form.username" 
          required 
          placeholder="请输入用户名或邮箱"
        />
        <div v-if="errors.username" class="error-message">{{ errors.username }}</div>
      </div>
      
      <div class="form-group">
        <label for="password">密码</label>
        <input 
          type="password" 
          id="password" 
          v-model="form.password" 
          required 
          placeholder="请输入密码"
        />
        <div v-if="errors.password" class="error-message">{{ errors.password }}</div>
      </div>

      <div class="form-group">
        <label for="captcha">验证码</label>
        <div class="captcha-container">
          <input 
            type="text" 
            id="captcha" 
            v-model="form.captcha_code" 
            required 
            placeholder="请输入验证码"
            maxlength="6"
          />
          <img 
            v-if="captchaUrl" 
            :src="captchaUrl" 
            alt="验证码" 
            class="captcha-image"
            @click="refreshCaptcha"
          />
        </div>
        <div v-if="errors.captcha" class="error-message">{{ errors.captcha }}</div>
      </div>
      
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '登录中...' : '登录' }}
      </button>
      
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </form>
    
    <div class="register-link">
      还没有账号？<router-link to="/register">立即注册</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import apiClient from '../services/api'

interface LoginForm {
  username: string
  password: string
  captcha_code: string
  captcha_id: string
}

interface LoginFormErrors {
  username: string
  password: string
  captcha: string
}

const router = useRouter()
const authStore = useAuthStore()

// 创建表单状态
const form = reactive<LoginForm>({
  username: '',
  password: '',
  captcha_code: '',
  captcha_id: ''
})

// 表单错误
const errors = reactive<LoginFormErrors>({
  username: '',
  password: '',
  captcha: ''
})

// 表单状态
const isSubmitting = computed(() => authStore.isLoading)
const successMessage = ref('')
const errorMessage = ref('')
const captchaUrl = ref('')

// 重置表单
const resetForm = () => {
  form.username = ''
  form.password = ''
  form.captcha_code = ''
  form.captcha_id = ''
  
  errors.username = ''
  errors.password = ''
  errors.captcha = ''
  
  successMessage.value = ''
  errorMessage.value = ''
}

// 获取验证码
const getCaptcha = async () => {
  try {
    const response = await apiClient.get('/captcha/generate', {
      responseType: 'blob'
    })
    const captchaId = response.headers['x-captcha-id']
    form.captcha_id = captchaId
    captchaUrl.value = URL.createObjectURL(response.data)
  } catch (error) {
    console.error('获取验证码失败:', error)
    errorMessage.value = '获取验证码失败，请刷新页面重试'
  }
}

// 刷新验证码
const refreshCaptcha = () => {
  if (captchaUrl.value) {
    URL.revokeObjectURL(captchaUrl.value)
  }
  getCaptcha()
}

// 验证表单
const validateForm = () => {
  let isValid = true
  
  // 重置错误
  errors.username = ''
  errors.password = ''
  errors.captcha = ''
  
  // 验证用户名/邮箱
  if (!form.username.trim()) {
    errors.username = '请输入用户名或邮箱'
    isValid = false
  }
  
  // 验证密码
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 8) {
    errors.password = '密码长度至少为8个字符'
    isValid = false
  }

  // 验证验证码
  if (!form.captcha_code) {
    errors.captcha = '请输入验证码'
    isValid = false
  } else if (form.captcha_code.length !== 6) {
    errors.captcha = '验证码必须是6位'
    isValid = false
  }
  
  return isValid
}

const login = async () => {
  // 表单验证
  if (!validateForm()) {
    return
  }
  
  // 重置消息
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    // 使用authStore进行登录
    await authStore.login(form.username, form.password, form.captcha_id, form.captcha_code)
    
    // 登录成功
    successMessage.value = '登录成功！正在跳转...'
    
    // 重置表单
    resetForm()
    
    // 延迟跳转到首页
    setTimeout(() => {
      router.push('/')
    }, 1000)
  } catch (error: any) {
    // 处理登录失败情况
    if (error.response) {
      // 服务器返回了错误信息
      errorMessage.value = error.response.data.detail || '登录失败，请检查用户名和密码'
      
      // 处理特定错误
      if (error.response.data.detail === '用户名或密码错误') {
        errors.password = '用户名或密码错误'
      } else if (error.response.data.detail === '验证码错误' || error.response.data.detail === '验证码已过期或不存在') {
        errors.captcha = error.response.data.detail
        refreshCaptcha()
      }
    } else {
      // 网络错误或其他错误
      errorMessage.value = '登录失败，请检查网络连接后重试'
    }
  }
}

// 组件挂载时获取验证码
onMounted(() => {
  getCaptcha()
})
</script>

<style scoped>
.login-container {
  max-width: 480px;
  margin: 0 auto;
  padding: 20px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.captcha-container {
  display: flex;
  gap: 8px;
  align-items: center;
}

.captcha-image {
  height: 40px;
  cursor: pointer;
  border-radius: 4px;
}

label {
  font-weight: bold;
}

input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

input#captcha {
  width: 120px;
}

button {
  padding: 12px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:disabled {
  background-color: #9e9e9e;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #3e8e41;
}

.error-message {
  color: #f44336;
  font-size: 14px;
  margin-top: 4px;
}

.success-message {
  color: #4caf50;
  font-size: 14px;
  margin-top: 8px;
}

.register-link {
  margin-top: 20px;
  text-align: center;
}

.register-link a {
  color: #3498db;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style> 