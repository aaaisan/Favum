<template>
  <div class="register-container">
    <h1>用户注册</h1>
    <form @submit.prevent="register" class="register-form">
      <div class="form-group">
        <label for="username">用户名</label>
        <input 
          type="text" 
          id="username" 
          v-model="form.username" 
          required 
          placeholder="请输入用户名"
        />
        <div v-if="errors.username" class="error-message">{{ errors.username }}</div>
      </div>
      
      <div class="form-group">
        <label for="email">邮箱</label>
        <input 
          type="email" 
          id="email" 
          v-model="form.email" 
          required 
          placeholder="请输入邮箱"
        />
        <div v-if="errors.email" class="error-message">{{ errors.email }}</div>
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
        <label for="confirmPassword">确认密码</label>
        <input 
          type="password" 
          id="confirmPassword" 
          v-model="form.confirmPassword" 
          required 
          placeholder="请再次输入密码"
        />
        <div v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</div>
      </div>
      
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '注册中...' : '注册' }}
      </button>
      
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </form>
    
    <div class="login-link">
      已有账号？<router-link to="/login">点击登录</router-link>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { validateRegisterForm, type RegisterForm, type RegisterFormErrors } from '../validators/register-form'

const router = useRouter()
const authStore = useAuthStore()

// 创建表单状态
const form = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  bio: ''
})

// 表单错误
const errors = reactive<RegisterFormErrors>({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 表单状态
const isSubmitting = computed(() => authStore.isLoading)
const successMessage = ref('')
const errorMessage = ref('')

// 重置表单
const resetForm = () => {
  form.username = ''
  form.email = ''
  form.password = ''
  form.confirmPassword = ''
  form.bio = ''
  
  errors.username = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''
  
  successMessage.value = ''
  errorMessage.value = ''
}

// 验证表单
const validateForm = () => {
  return validateRegisterForm(form, errors)
}

const register = async () => {
  // 表单验证
  if (!validateForm()) {
    return
  }
  
  // 重置消息
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    // 使用authStore进行注册
    await authStore.register(
      form.username,
      form.email,
      form.password
    )
    
    // 注册成功
    successMessage.value = '注册成功！正在跳转到登录页面...'
    
    // 重置表单
    resetForm()
    
    // 延迟跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    // 处理注册失败情况
    if (error.response) {
      // 服务器返回了错误信息
      errorMessage.value = error.response.data.detail || '注册失败，请稍后重试'
      
      // 处理特定字段的错误
      if (error.response.data.detail === '用户名已被使用') {
        errors.username = '该用户名已被注册'
      } else if (error.response.data.detail === '邮箱已被注册') {
        errors.email = '该邮箱已被注册'
      }
    } else {
      // 网络错误或其他错误
      errorMessage.value = '注册失败，请检查网络连接后重试'
    }
  }
}
</script>

<style scoped>
.register-container {
  max-width: 480px;
  margin: 0 auto;
  padding: 20px;
}

.register-form {
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

label {
  font-weight: bold;
}

input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
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

.login-link {
  margin-top: 20px;
  text-align: center;
}

.login-link a {
  color: #3498db;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style> 
