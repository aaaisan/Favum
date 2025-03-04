<template>
  <div class="login-container">
    <h1>登录</h1>
    <form @submit.prevent="handleSubmit" class="login-form">
      <div class="form-group">
        <label for="username">用户名</label>
        <input
          id="username"
          v-model="form.username"
          type="text"
          :class="{ error: errors.username }"
        />
        <span class="error-message" v-if="errors.username">{{ errors.username }}</span>
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          :class="{ error: errors.password }"
        />
        <span class="error-message" v-if="errors.password">{{ errors.password }}</span>
      </div>

      <div class="form-group">
        <label>验证码</label>
        <Captcha
          v-model="form.captcha_code"
          :error="errors.captcha_code"
          @refresh="id => handleCaptchaRefresh(id)"
        />
      </div>

      <div class="error-message" v-if="errorMessage">{{ errorMessage }}</div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '登录中...' : '登录' }}
      </button>

      <div class="form-footer">
        <router-link to="/register">还没有账号？立即注册</router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useLoginForm } from '../composables/useLoginForm'
import { useAuthStore } from '../stores/auth'
import Captcha from '../components/Captcha.vue'

const router = useRouter()
const authStore = useAuthStore()
const { 
  form, 
  errors, 
  isSubmitting, 
  errorMessage, 
  validate, 
  resetForm,
  handleCaptchaRefresh 
} = useLoginForm()

const handleSubmit = async () => {
  console.log('提交登录表单，验证码ID:', form.captcha_id)
  console.log('提交登录表单，验证码内容:', form.captcha_code)
  console.log('提交登录表单，完整数据:', JSON.stringify(form))
  
  if (!validate()) {
    console.log('表单验证失败')
    return
  }

  try {
    isSubmitting.value = true
    console.log('开始登录请求，数据:', JSON.stringify(form))
    await authStore.login(form)
    resetForm()
    router.push('/')
  } catch (error: any) {
    console.error('登录失败:', error)
    if (error.response) {
      console.error('响应状态:', error.response.status)
      console.error('响应数据:', error.response.data)
    }
    errorMessage.value = error.response?.data?.detail || '登录失败'
    if (error.response?.status === 400) {
      console.log('登录失败，刷新验证码')
      handleCaptchaRefresh()
    }
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
}

.login-form {
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

input {
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
}

button {
  padding: 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover:not(:disabled) {
  background-color: #2980b9;
}

button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
}

.form-footer a {
  color: #3498db;
  text-decoration: none;
}

.form-footer a:hover {
  text-decoration: underline;
}
</style> 