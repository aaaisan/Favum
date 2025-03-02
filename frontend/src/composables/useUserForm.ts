import { reactive, ref } from 'vue'
import { 
  type UserForm, 
  type UserFormErrors, 
  validateUserForm, 
  clearUserFormErrors 
} from '../validators/user'
import type { UserUpdateRequest } from '../types'

/**
 * 用户表单组合式函数
 * @param initialValues - 初始表单值
 * @returns 表单状态和方法
 */
export function useUserForm(initialValues: Partial<UserForm> = {}) {
  // 表单数据
  const form = reactive<UserForm>({
    username: initialValues.username || '',
    email: initialValues.email || '',
    password: '',
    confirmPassword: '',
    bio: initialValues.bio || ''
  })
  
  // 表单错误
  const errors = reactive<UserFormErrors>({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  
  // 表单状态
  const isSubmitting = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')
  
  /**
   * 重置表单
   */
  const resetForm = () => {
    form.username = initialValues.username || ''
    form.email = initialValues.email || ''
    form.bio = initialValues.bio || ''
    form.password = ''
    form.confirmPassword = ''
    clearUserFormErrors(errors)
    successMessage.value = ''
    errorMessage.value = ''
  }
  
  /**
   * 验证表单
   * @param options - 验证选项
   * @returns 是否验证通过
   */
  const validate = (options: { isPasswordRequired: boolean } = { isPasswordRequired: true }) => {
    return validateUserForm(form, errors, options)
  }
  
  /**
   * 获取更新数据对象
   * @returns 用于API请求的数据对象
   */
  const getUpdateData = (): UserUpdateRequest => {
    const updateData: UserUpdateRequest = {
      username: form.username,
      email: form.email,
      bio: form.bio
    }
    
    if (form.password) {
      updateData.password = form.password
    }
    
    return updateData
  }
  
  return {
    form,
    errors,
    isSubmitting,
    successMessage,
    errorMessage,
    resetForm,
    validate,
    getUpdateData
  }
} 