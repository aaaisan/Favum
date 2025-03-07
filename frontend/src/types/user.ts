// 用户基本信息接口
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  bio: string | null;
  avatar_url: string | null;
  created_at: string;
  is_active: boolean;
  is_deleted: boolean;
}

// 用户列表响应接口
export interface UserList {
  users: User[];
  total: number;
  page_size: number;
}

// 用户统计信息接口
export interface UserStats {
  post_count: number;
  comment_count: number;
  reputation: number;
  join_date: string;
  last_login: string | null;
}

// 用户角色枚举
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
  MODERATOR = 'moderator'
}

// 用户更新请求接口
export interface UserUpdateRequest {
  username: string;
  email: string;
  bio: string | null;
  password?: string;
}

// 用户资料表单接口
export interface UserProfileForm {
  username: string;
  email: string;
  bio: string;
  password: string;
  confirmPassword: string;
}

// 用户资料表单错误接口
export interface UserProfileFormErrors {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
} 