/**
 * 注册表单验证模块
 * 这个文件包含专门用于注册表单的验证逻辑
 */

// 导入基础验证函数
import { isNotEmpty, isMinLength, isValidEmail } from './common'

// 表单接口
export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  bio?: string
}

// 错误接口
export interface RegisterFormErrors {
  username: string
  email: string
  password: string
  confirmPassword: string
}

/**
 * 验证注册表单
 * 一个简单的表单验证函数，专门用于注册页面
 */
export function validateRegisterForm(form: RegisterForm, errors: RegisterFormErrors): boolean {
  // 重置错误信息
  errors.username = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''
  
  let isValid = true
  
  // 验证用户名
  if (!isNotEmpty(form.username)) {
    errors.username = '用户名不能为空'
    isValid = false
  } else if (!isMinLength(form.username, 3)) {
    errors.username = '用户名至少需要3个字符'
    isValid = false
  }
  
  // 验证邮箱
  if (!isNotEmpty(form.email)) {
    errors.email = '邮箱不能为空'
    isValid = false
  } else if (!isValidEmail(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    isValid = false
  }
  
  // 验证密码
  if (!isNotEmpty(form.password)) {
    errors.password = '密码不能为空'
    isValid = false
  } else if (!isMinLength(form.password, 6)) {
    errors.password = '密码至少需要6个字符'
    isValid = false
  }
  
  // 验证确认密码
  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
    isValid = false
  }
  
  return isValid
} 