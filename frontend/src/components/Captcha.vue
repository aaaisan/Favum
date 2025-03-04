<template>
  <div class="captcha-container">
    <div class="captcha-input">
      <input
        type="text"
        v-model="code"
        placeholder="请输入验证码"
        maxlength="6"
        :class="{ error: error }"
        @input="handleInput"
      />
      <div class="captcha-image" @click="refreshCaptcha">
        <img v-if="captchaImage" :src="'data:image/png;base64,' + captchaImage" alt="验证码" />
        <div v-else class="loading">加载中...</div>
      </div>
      <button type="button" class="refresh-btn" @click="refreshCaptcha" title="刷新验证码">
        ↻
      </button>
    </div>
    <span v-if="error" class="error-message">{{ error }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useCaptcha } from '../composables/useCaptcha'

const props = defineProps<{
  modelValue?: string;
  error?: string;
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'refresh', id: string): void;
}>()

const code = ref(props.modelValue || '')
const { captchaImage, captchaId, getCaptcha, isLoading } = useCaptcha()

// 监听 modelValue 的变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== code.value) {
    code.value = newValue || ''
  }
})

// 监听 captchaId 的变化，确保在 ID 变化时通知父组件
watch(() => captchaId.value, (newId) => {
  if (newId) {
    console.log('验证码ID已更新，通知父组件:', newId)
    emit('refresh', newId)
  }
})

const handleInput = () => {
  emit('update:modelValue', code.value)
}

const refreshCaptcha = async () => {
  try {
    code.value = ''
    emit('update:modelValue', '')
    console.log('刷新验证码...')
    await getCaptcha()
    
    // 确保验证码ID已设置
    if (captchaId.value) {
      console.log('刷新后的验证码ID:', captchaId.value)
      emit('refresh', captchaId.value)
    } else {
      console.error('刷新验证码后ID为空')
    }
  } catch (err) {
    console.error('刷新验证码失败:', err)
  }
}

onMounted(async () => {
  try {
    console.log('Captcha组件已挂载，获取验证码...')
    await getCaptcha()
    
    // 确保验证码ID已设置
    if (captchaId.value) {
      console.log('初始验证码ID:', captchaId.value)
      emit('refresh', captchaId.value)
    } else {
      console.error('初始验证码ID为空')
    }
  } catch (err) {
    console.error('初始化验证码失败:', err)
  }
})
</script>

<style scoped>
.captcha-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.captcha-input {
  display: flex;
  gap: 8px;
  align-items: center;
}

input {
  width: 120px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

input.error {
  border-color: #e74c3c;
}

.captcha-image {
  width: 120px;
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 14px;
}

.refresh-btn {
  padding: 8px;
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.refresh-btn:hover {
  color: #333;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
}
</style> 