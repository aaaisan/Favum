// 用户基本信息接口
export interface User {
  id?: number;
  username: string;
  email: string;
  role: string;
  created_at?: string;
  last_login?: string;
  bio?: string;
  is_active?: boolean;
}

// 用户列表响应接口
export interface UserList {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

// 用户统计信息接口
export interface UserStats {
  postCount: number;
  commentCount: number;
  favoriteCount: number;
  likeCount: number;
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
  username?: string;
  email?: string;
  bio?: string;
  password?: string;
} 