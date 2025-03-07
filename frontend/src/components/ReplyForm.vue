<template>
  <div class="reply-form">
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="content">回复内容</label>
        <textarea 
          id="content" 
          v-model="form.content" 
          rows="4"
          :class="{ error: errors.content }"
          :placeholder="placeholder"
        ></textarea>
        <span class="error-message" v-if="errors.content">{{ errors.content }}</span>
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

      <div class="form-actions">
        <button type="button" class="cancel-button" @click="$emit('cancel')" v-if="showCancel">
          取消
        </button>
        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '发送中...' : '发送回复' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useReplyForm } from '../composables/useReplyForm'
import { useReplyStore } from '../stores/reply'
import Captcha from './Captcha.vue'

const props = defineProps<{
  postId: number
  parentId?: number
  showCancel?: boolean
}>()

const emit = defineEmits<{
  (e: 'success', reply: any): void
  (e: 'cancel'): void
}>()

const placeholder = computed(() => {
  return props.parentId ? '回复评论...' : '写下你的评论...'
})

const replyStore = useReplyStore()
const {
  form,
  errors,
  isSubmitting,
  successMessage,
  errorMessage,
  validate,
  resetForm,
  handleCaptchaRefresh
} = useReplyForm(props.postId, props.parentId)

const handleSubmit = async () => {
  if (!validate()) return

  try {
    isSubmitting.value = true
    const reply = await replyStore.createReply(form)
    successMessage.value = '回复成功！'
    resetForm()
    emit('success', reply)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '回复失败'
    if (error.response?.status === 400) {
      handleCaptchaRefresh()
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.reply-form {
  margin: 20px 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

label {
  font-weight: 500;
  color: #2c3e50;
}

textarea {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  resize: vertical;
}

textarea.error {
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

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button[type="submit"] {
  background-color: #3498db;
  color: white;
}

button[type="submit"]:hover:not(:disabled) {
  background-color: #2980b9;
}

button[type="submit"]:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: #e0e0e0;
  color: #666;
}

.cancel-button:hover {
  background-color: #d0d0d0;
}
</style> 