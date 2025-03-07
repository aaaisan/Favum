import type { User } from './user'

export interface LoginForm {
  username: string
  password: string
  captcha_id: string
  captcha_code: string
}

export interface LoginFormErrors {
  username: string
  password: string
  captcha_code: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  bio: string
  captcha_id: string
  captcha_code: string
}

export interface RegisterFormErrors {
  username: string
  email: string
  password: string
  confirmPassword: string
  captcha_code: string
} 