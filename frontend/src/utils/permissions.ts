import { UserRole } from '../types/user'
import type { User } from '../types/user'

/**
 * 检查用户是否拥有指定角色
 * @param user 用户对象
 * @param role 角色或角色数组
 * @returns 用户是否拥有指定角色
 */
export function hasRole(user: User | null, role: string | string[]): boolean {
  if (!user) return false
  
  const roles = Array.isArray(role) ? role : [role]
  return roles.includes(user.role)
}

/**
 * 检查用户是否是管理员（包括超级管理员）
 * @param user 用户对象
 * @returns 用户是否是管理员
 */
export function isAdmin(user: User | null): boolean {
  if (!user) return false
  return user.role === UserRole.ADMIN || user.role === UserRole.SUPER_ADMIN
}

/**
 * 检查用户是否是超级管理员
 * @param user 用户对象
 * @returns 用户是否是超级管理员
 */
export function isSuperAdmin(user: User | null): boolean {
  if (!user) return false
  return user.role === UserRole.SUPER_ADMIN
}

/**
 * 检查用户是否是版主
 * @param user 用户对象
 * @returns 用户是否是版主
 */
export function isModerator(user: User | null): boolean {
  if (!user) return false
  return user.role === UserRole.MODERATOR
}

/**
 * 检查用户是否可以访问仪表盘
 * @param user 用户对象
 * @returns 用户是否可以访问仪表盘
 */
export function canAccessDashboard(user: User | null): boolean {
  if (!user) return false
  return isAdmin(user) || isModerator(user)
}

/**
 * 检查用户是否可以管理用户（仅管理员可以）
 * @param user 用户对象
 * @returns 用户是否可以管理用户
 */
export function canManageUsers(user: User | null): boolean {
  return isAdmin(user)
}

/**
 * 检查用户是否可以管理分类（仅管理员可以）
 * @param user 用户对象
 * @returns 用户是否可以管理分类
 */
export function canManageCategories(user: User | null): boolean {
  return isAdmin(user)
}

/**
 * 检查用户是否可以管理标签（仅管理员可以）
 * @param user 用户对象
 * @returns 用户是否可以管理标签
 */
export function canManageTags(user: User | null): boolean {
  return isAdmin(user)
}

/**
 * 检查用户是否可以管理帖子（管理员和版主都可以）
 * @param user 用户对象
 * @returns 用户是否可以管理帖子
 */
export function canManagePosts(user: User | null): boolean {
  if (!user) return false
  return isAdmin(user) || isModerator(user)
}

/**
 * 检查用户是否可以编辑指定帖子
 * @param user 用户对象
 * @param authorId 帖子作者ID
 * @returns 用户是否可以编辑帖子
 */
export function canEditPost(user: User | null, authorId: number): boolean {
  if (!user) return false
  
  // 管理员和版主可以编辑任何帖子
  if (isAdmin(user) || isModerator(user)) return true
  
  // 普通用户只能编辑自己的帖子
  return user.id === authorId
}

/**
 * 检查用户是否可以删除指定帖子
 * @param user 用户对象
 * @param authorId 帖子作者ID
 * @returns 用户是否可以删除帖子
 */
export function canDeletePost(user: User | null, authorId: number): boolean {
  if (!user) return false
  
  // 管理员和版主可以删除任何帖子
  if (isAdmin(user) || isModerator(user)) return true
  
  // 普通用户只能删除自己的帖子
  return user.id === authorId
} 