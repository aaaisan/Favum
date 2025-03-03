<template>
  <div class="register-container">
    <h1>用户注册</h1>
    <form @submit.prevent="handleSubmit" class="register-form">
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
        <label for="password">密码</label>
        <input 
          type="password" 
          id="password" 
          v-model="form.password" 
          :class="{ error: errors.password }"
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
        />
        <span class="error-message" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
      </div>
      
      <div class="form-group">
        <label for="bio">个人简介 (可选)</label>
        <textarea 
          id="bio" 
          v-model="form.bio" 
          rows="3"
        ></textarea>
      </div>

      <div class="error-message" v-if="errorMessage">{{ errorMessage }}</div>
      <div class="success-message" v-if="successMessage">{{ successMessage }}</div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? '注册中...' : '注册' }}
      </button>

      <div class="form-footer">
        <router-link to="/login">已有账号？点击登录</router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useRegisterForm } from '../composables/useRegisterForm'

const router = useRouter()
const authStore = useAuthStore()
const {
  form,
  errors,
  isSubmitting,
  successMessage,
  errorMessage,
  resetForm,
  validate
} = useRegisterForm()

const handleSubmit = async () => {
  if (!validate()) return

  try {
    isSubmitting.value = true
    await authStore.register(form.username, form.email, form.password)
    successMessage.value = '注册成功！正在跳转到登录页面...'
    resetForm()
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '注册失败'
    if (error.response?.data?.detail === '用户名已被使用') {
      errors.username = '该用户名已被注册'
    } else if (error.response?.data?.detail === '邮箱已被注册') {
      errors.email = '该邮箱已被注册'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.register-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
}

.register-form {
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

input, textarea {
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

.success-message {
  color: #2ecc71;
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
