import type { RegisterForm, RegisterFormErrors } from '../types/auth'

/**
 * 验证注册表单
 * @param form - 表单数据
 * @param errors - 错误对象
 * @returns 是否验证通过
 */
export function validateRegisterForm(form: RegisterForm, errors: RegisterFormErrors): boolean {
  let isValid = true

  // 清除之前的错误
  clearRegisterFormErrors(errors)

  // 验证用户名
  if (!form.username) {
    errors.username = '请输入用户名'
    isValid = false
  } else if (form.username.length < 3) {
    errors.username = '用户名长度不能少于3个字符'
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
    errors.password = '密码长度不能少于6个字符'
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

  return isValid
}

export function clearRegisterFormErrors(errors: RegisterFormErrors): void {
  errors.username = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''
} 