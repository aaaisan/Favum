import { isNotEmpty, isMinLength, isValidEmail, isEqual } from './common'

/**
 * 用户表单错误接口
 */
export interface UserFormErrors {
  username: string
  email: string
  password: string
  confirmPassword: string
}

/**
 * 用户注册/编辑表单接口
 */
export interface UserForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  bio?: string
}

/**
 * 清除用户表单错误
 * @param errors - 错误对象
 */
export function clearUserFormErrors(errors: UserFormErrors): void {
  errors.username = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''
}

/**
 * 验证用户名
 * @param username - 用户名
 * @param errors - 错误对象
 * @param minLength - 最小长度，默认为3
 * @returns 是否验证通过
 */
export function validateUsername(
  username: string, 
  errors: UserFormErrors,
  minLength: number = 3
): boolean {
  if (!isNotEmpty(username)) {
    errors.username = '用户名不能为空'
    return false
  }
  
  if (!isMinLength(username, minLength)) {
    errors.username = `用户名至少需要${minLength}个字符`
    return false
  }
  
  return true
}

/**
 * 验证邮箱
 * @param email - 邮箱地址
 * @param errors - 错误对象
 * @returns 是否验证通过
 */
export function validateEmail(
  email: string, 
  errors: UserFormErrors
): boolean {
  if (!isNotEmpty(email)) {
    errors.email = '邮箱不能为空'
    return false
  }
  
  if (!isValidEmail(email)) {
    errors.email = '请输入有效的邮箱地址'
    return false
  }
  
  return true
}

/**
 * 验证密码
 * @param password - 密码
 * @param errors - 错误对象
 * @param isRequired - 是否为必填，默认为true
 * @param minLength - 最小长度，默认为6
 * @returns 是否验证通过
 */
export function validatePassword(
  password: string, 
  errors: UserFormErrors,
  isRequired: boolean = true,
  minLength: number = 6
): boolean {
  if (isRequired && !isNotEmpty(password)) {
    errors.password = '密码不能为空'
    return false
  }
  
  if (isNotEmpty(password) && !isMinLength(password, minLength)) {
    errors.password = `密码至少需要${minLength}个字符`
    return false
  }
  
  return true
}

/**
 * 验证确认密码
 * @param password - 密码
 * @param confirmPassword - 确认密码
 * @param errors - 错误对象
 * @returns 是否验证通过
 */
export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
  errors: UserFormErrors
): boolean {
  if (isNotEmpty(password) && !isEqual(password, confirmPassword)) {
    errors.confirmPassword = '两次输入的密码不一致'
    return false
  }
  
  return true
}

/**
 * 验证整个用户表单
 * @param form - 表单数据
 * @param errors - 错误对象
 * @param options - 验证选项
 * @returns 是否验证通过
 */
export function validateUserForm(
  form: UserForm, 
  errors: UserFormErrors,
  options: { 
    isPasswordRequired: boolean 
  } = { 
    isPasswordRequired: true 
  }
): boolean {
  clearUserFormErrors(errors)
  
  const isUsernameValid = validateUsername(form.username, errors)
  const isEmailValid = validateEmail(form.email, errors)
  const isPasswordValid = validatePassword(form.password, errors, options.isPasswordRequired)
  const isConfirmPasswordValid = validateConfirmPassword(form.password, form.confirmPassword, errors)
  
  return isUsernameValid && isEmailValid && isPasswordValid && isConfirmPasswordValid
}

// 提供更简单的重载版本用于组件内直接调用
export function validateUserFormSimple(form: UserForm, errors: UserFormErrors): boolean {
  return validateUserForm(form, errors, { isPasswordRequired: true });
} 