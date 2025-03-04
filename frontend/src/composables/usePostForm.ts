import { reactive, ref } from 'vue'
import type { PostForm, PostFormErrors } from '../types/post'
import { useCaptcha } from './useCaptcha'

export function usePostForm() {
  const { captchaId, getCaptcha } = useCaptcha()
  
  const form = reactive<PostForm>({
    title: '',
    content: '',
    category_id: 0,
    tags: [],
    captcha_id: '',
    captcha_code: ''
  })
  
  const errors = reactive<PostFormErrors>({
    title: '',
    content: '',
    category_id: '',
    captcha_code: ''
  })
  
  const isSubmitting = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')
  
  const validate = () => {
    let isValid = true
    
    // 清除之前的错误
    errors.title = ''
    errors.content = ''
    errors.category_id = ''
    errors.captcha_code = ''
    
    // 验证标题
    if (!form.title) {
      errors.title = '请输入标题'
      isValid = false
    } else if (form.title.length < 5) {
      errors.title = '标题至少需要5个字符'
      isValid = false
    }
    
    // 验证内容
    if (!form.content) {
      errors.content = '请输入内容'
      isValid = false
    } else if (form.content.length < 10) {
      errors.content = '内容至少需要10个字符'
      isValid = false
    }
    
    // 验证分类
    if (!form.category_id) {
      errors.category_id = '请选择分类'
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
    form.title = ''
    form.content = ''
    form.category_id = 0
    form.tags = []
    form.captcha_code = ''
    errors.title = ''
    errors.content = ''
    errors.category_id = ''
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