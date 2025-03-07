import { reactive, ref } from 'vue'
import type { RegisterForm, RegisterFormErrors } from '../types/auth'
import { useCaptcha } from './useCaptcha'

export function useRegisterForm() {
  const { captchaId, getCaptcha } = useCaptcha()
  
  const form = reactive<RegisterForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    bio: '',
    captcha_id: '',
    captcha_code: ''
  })
  
  const errors = reactive<RegisterFormErrors>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    captcha_code: ''
  })
  
  const isSubmitting = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')
  
  const validate = () => {
    let isValid = true
    
    // 清除之前的错误
    errors.username = ''
    errors.email = ''
    errors.password = ''
    errors.confirmPassword = ''
    errors.captcha_code = ''
    
    // 验证用户名
    if (!form.username) {
      errors.username = '请输入用户名'
      isValid = false
    } else if (form.username.length < 3) {
      errors.username = '用户名至少需要3个字符'
      isValid = false
    }
    
    // 验证邮箱
    if (!form.email) {
      errors.email = '请输入邮箱'
      isValid = false
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errors.email = '请输入有效的邮箱地址'
      isValid = false
    }
    
    // 验证密码
    if (!form.password) {
      errors.password = '请输入密码'
      isValid = false
    } else if (form.password.length < 6) {
      errors.password = '密码至少需要6个字符'
      isValid = false
    }
    
    // 验证确认密码
    if (!form.confirmPassword) {
      errors.confirmPassword = '请确认密码'
      isValid = false
    } else if (form.confirmPassword !== form.password) {
      errors.confirmPassword = '两次输入的密码不一致'
      isValid = false
    }
    
    // 验证验证码
    if (!form.captcha_code) {
      errors.captcha_code = '请输入验证码'
      isValid = false
    }
    
    // 确保验证码ID存在
    if (!form.captcha_id) {
      errors.captcha_code = '验证码未加载，请刷新验证码'
      isValid = false
    }
    
    return isValid
  }
  
  const resetForm = () => {
    form.username = ''
    form.email = ''
    form.password = ''
    form.confirmPassword = ''
    form.bio = ''
    form.captcha_code = ''
    errors.username = ''
    errors.email = ''
    errors.password = ''
    errors.confirmPassword = ''
    errors.captcha_code = ''
    errorMessage.value = ''
    successMessage.value = ''
  }
  
  const handleCaptchaRefresh = async (id?: string) => {
    if (!id) {
      await getCaptcha()
      // 确保captchaId.value有值后再设置
      console.log('设置验证码ID:', captchaId.value)
      form.captcha_id = captchaId.value
    } else {
      console.log('从参数设置验证码ID:', id)
      form.captcha_id = id
    }
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