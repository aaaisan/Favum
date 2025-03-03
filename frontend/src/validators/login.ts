import type { LoginForm, LoginFormErrors } from '../types'

export function validateLoginForm(form: LoginForm, errors: LoginFormErrors): boolean {
  let isValid = true

  // 清除之前的错误
  clearLoginFormErrors(errors)

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

  return isValid
}

export function clearLoginFormErrors(errors: LoginFormErrors): void {
  errors.email = ''
  errors.password = ''
} 