import { UserRole } from '../types'

/**
 * 角色名称映射
 */
export const ROLE_NAMES: Record<string, string> = {
  [UserRole.USER]: '普通用户',
  [UserRole.ADMIN]: '管理员',
  [UserRole.SUPER_ADMIN]: '超级管理员',
  [UserRole.MODERATOR]: '版主'
}

/**
 * 格式化用户角色
 * @param role 角色代码
 * @returns 格式化后的角色名称
 */
export function formatRole(role: string): string {
  switch (role) {
    case 'admin':
      return '管理员';
    case 'super_admin':
      return '超级管理员';
    case 'moderator':
      return '版主';
    case 'user':
      return '普通用户';
    default:
      return role || '未知角色';
  }
}

/**
 * 获取角色徽章样式
 * @param role 角色代码
 * @returns 对应的样式类名
 */
export function getRoleBadgeClass(role: string): string {
  switch (role) {
    case 'admin':
      return 'admin';
    case 'super_admin':
      return 'super-admin';
    case 'moderator':
      return 'moderator';
    default:
      return 'user';
  }
}

/**
 * 检查是否为管理员角色
 * @param role - 角色标识
 * @returns 是否为管理员
 */
export function isAdminRole(role: string | undefined): boolean {
  return role === UserRole.ADMIN || role === UserRole.SUPER_ADMIN
} 