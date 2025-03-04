import { reactive, ref } from 'vue'
import type { LoginForm, LoginFormErrors } from '../types/auth'
import { useCaptcha } from './useCaptcha'

export function useLoginForm() {
  const { captchaId, getCaptcha } = useCaptcha()
  
  const form = reactive<LoginForm>({
    username: '',
    password: '',
    captcha_id: '',
    captcha_code: ''
  })
  
  const errors = reactive<LoginFormErrors>({
    username: '',
    password: '',
    captcha_code: ''
  })
  
  const isSubmitting = ref(false)
  const errorMessage = ref('')
  
  const validate = () => {
    let isValid = true
    
    // 清除之前的错误
    errors.username = ''
    errors.password = ''
    errors.captcha_code = ''
    
    // 验证用户名
    if (!form.username) {
      errors.username = '请输入用户名'
      isValid = false
    }
    
    // 验证密码
    if (!form.password) {
      errors.password = '请输入密码'
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
    form.username = ''
    form.password = ''
    form.captcha_code = ''
    errors.username = ''
    errors.password = ''
    errors.captcha_code = ''
    errorMessage.value = ''
  }
  
  const handleCaptchaRefresh = async (id?: string) => {
    try {
      console.log('登录表单刷新验证码，当前验证码ID:', captchaId.value)
      
      if (id) {
        // 如果提供了ID，直接使用
        console.log('使用提供的验证码ID:', id)
        form.captcha_id = id
      } else {
        // 否则获取新的验证码
        await getCaptcha()
        console.log('获取新验证码后，验证码ID:', captchaId.value)
        form.captcha_id = captchaId.value
      }
      
      console.log('设置表单验证码ID:', form.captcha_id)
      form.captcha_code = ''
    } catch (err) {
      console.error('刷新验证码失败:', err)
    }
  }
  
  // 初始化验证码
  handleCaptchaRefresh()
  
  return {
    form,
    errors,
    isSubmitting,
    errorMessage,
    validate,
    resetForm,
    handleCaptchaRefresh
  }
} 