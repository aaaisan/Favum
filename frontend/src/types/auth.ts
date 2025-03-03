import type { User } from './user'

export interface LoginForm {
  email: string
  password: string
}

export interface LoginFormErrors {
  email: string
  password: string
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
}

export interface RegisterFormErrors {
  username: string
  email: string
  password: string
  confirmPassword: string
} 