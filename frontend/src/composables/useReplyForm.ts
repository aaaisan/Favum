import { reactive, ref } from 'vue'
import type { ReplyForm, ReplyFormErrors } from '../types/post'
import { useCaptcha } from './useCaptcha'

export function useReplyForm(postId: number, parentId?: number) {
  const { captchaId, getCaptcha } = useCaptcha()
  
  const form = reactive<ReplyForm>({
    content: '',
    post_id: postId,
    parent_id: parentId,
    captcha_id: '',
    captcha_code: ''
  })
  
  const errors = reactive<ReplyFormErrors>({
    content: '',
    captcha_code: ''
  })
  
  const isSubmitting = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')
  
  const validate = () => {
    let isValid = true
    
    // 清除之前的错误
    errors.content = ''
    errors.captcha_code = ''
    
    // 验证内容
    if (!form.content) {
      errors.content = '请输入回复内容'
      isValid = false
    } else if (form.content.length < 5) {
      errors.content = '回复内容至少需要5个字符'
      isValid = false
    }
    
    // 验证验证码
    if (!form.captcha_code) {
      errors.captcha_code = '请输入验证码'
      isValid = false
    }
    
    return isValid
  }
  
  const resetForm = () => {
    form.content = ''
    form.captcha_code = ''
    errors.content = ''
    errors.captcha_code = ''
    errorMessage.value = ''
    successMessage.value = ''
  }
  
  const handleCaptchaRefresh = async () => {
    await getCaptcha()
    form.captcha_id = captchaId.value
    form.captcha_code = ''
  }
  
  // 初始化验证码
  handleCaptchaRefresh()
  
  return {
    form,
    errors,
    isSubmitting,
    successMessage,
    errorMessage,
    validate,
    resetForm,
    handleCaptchaRefresh
  }
} 