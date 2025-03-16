"""
权限检查模块

提供权限检查相关的功能，包括：
- 角色权限定义
- 权限检查
- 资源所有权检查
"""

from typing import Optional, Dict, Any, List, Set, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from functools import lru_cache as memo
from enum import Enum, auto

from ..db.models import User
from .exceptions import PermissionError, UserNotFoundError
from .auth import get_current_user, require_active_user

class Role(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 管理员
    MODERATOR = "moderator"  # 版主
    USER = "user"  # 普通用户
    GUEST = "guest"  # 访客

class Permission(str, Enum):
    """权限枚举"""
    # 帖子权限
    CREATE_POST = "create_post"  # 创建帖子
    READ_POST = "read_post"  # 读取帖子
    UPDATE_POST = "update_post"  # 更新帖子
    DELETE_POST = "delete_post"  # 删除帖子
    RESTORE_POST = "restore_post"  # 恢复帖子
    
    # 评论权限
    CREATE_COMMENT = "create_comment"  # 创建评论
    READ_COMMENT = "read_comment"  # 读取评论
    UPDATE_COMMENT = "update_comment"  # 更新评论
    DELETE_COMMENT = "delete_comment"  # 删除评论
    
    # 用户权限
    UPDATE_PROFILE = "update_profile"  # 更新个人资料
    READ_PROFILE = "read_profile"  # 读取个人资料
    
    # 管理权限
    MANAGE_USERS = "manage_users"  # 管理用户
    MANAGE_POSTS = "manage_posts"  # 管理帖子
    MANAGE_COMMENTS = "manage_comments"  # 管理评论
    MANAGE_TAGS = "manage_tags"  # 管理标签
    MANAGE_CATEGORIES = "manage_categories"  # 管理分类
    MANAGE_SECTIONS = "manage_sections"  # 管理版块

class PermissionChecker:
    """权限检查器类"""
    
    def __init__(self):
        """初始化权限检查器
        
        设置角色-权限映射关系
        """
        # 定义每个角色拥有的权限
        self.role_permissions = {
            Role.ADMIN: {
                Permission.CREATE_POST, Permission.READ_POST,
                Permission.UPDATE_POST, Permission.DELETE_POST,
                Permission.RESTORE_POST, Permission.CREATE_COMMENT,
                Permission.READ_COMMENT, Permission.UPDATE_COMMENT,
                Permission.DELETE_COMMENT, Permission.UPDATE_PROFILE,
                Permission.READ_PROFILE, Permission.MANAGE_USERS,
                Permission.MANAGE_POSTS, Permission.MANAGE_COMMENTS,
                Permission.MANAGE_TAGS, Permission.MANAGE_CATEGORIES,
                Permission.MANAGE_SECTIONS
            },
            Role.MODERATOR: {
                Permission.CREATE_POST, Permission.READ_POST,
                Permission.UPDATE_POST, Permission.DELETE_POST,
                Permission.CREATE_COMMENT, Permission.READ_COMMENT,
                Permission.UPDATE_COMMENT, Permission.DELETE_COMMENT,
                Permission.UPDATE_PROFILE, Permission.READ_PROFILE,
                Permission.MANAGE_POSTS, Permission.MANAGE_COMMENTS
            },
            Role.USER: {
                Permission.CREATE_POST, Permission.READ_POST,
                Permission.UPDATE_POST, Permission.DELETE_POST,
                Permission.CREATE_COMMENT, Permission.READ_COMMENT,
                Permission.UPDATE_COMMENT, Permission.DELETE_COMMENT,
                Permission.UPDATE_PROFILE, Permission.READ_PROFILE
            },
            Role.GUEST: {
                Permission.READ_POST, Permission.READ_COMMENT,
                Permission.READ_PROFILE
            }
        }
    
    async def has_permission(
        self,
        user: Optional[User],
        permission: Permission
    ) -> bool:
        """检查用户是否具有指定权限
        
        Args:
            user: 用户对象
            permission: 要检查的权限
            
        Returns:
            bool: 是否具有权限
        """
        if not user:
            return permission in self.role_permissions[Role.GUEST]
            
        user_role = user.role or Role.GUEST
        if user_role not in self.role_permissions:
            return False
            
        # 检查权限
        return permission in self.role_permissions[user_role]
    
    async def is_admin(
        self,
        user: Optional[User] = Depends(get_current_user)
    ) -> bool:
        """检查用户是否为管理员
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否为管理员
        """
        if not user:
            return False
        return user.role == Role.ADMIN
    
    async def is_moderator(
        self,
        user: Optional[User] = Depends(get_current_user)
    ) -> bool:
        """检查用户是否为版主
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否为版主
        """
        if not user:
            return False
        return user.role in [Role.ADMIN, Role.MODERATOR]
    
    async def check_permission(
        self,
        permission: Permission,
        user: Optional[User] = Depends(get_current_user)
    ) -> User:
        """检查用户是否具有指定权限,不具有则抛出异常
        
        Args:
            permission: 要检查的权限
            user: 用户对象
            
        Returns:
            User: 用户对象
            
        Raises:
            HTTPException: 当用户不具有权限时抛出
        """
        # 要求用户存在且激活
        user = require_active_user(user)
        
        # 检查权限
        if not await self.has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )
        return user
    
    async def check_owner(
        self,
        resource_owner_id: int,
        user: Optional[User] = Depends(get_current_user)
    ) -> User:
        """检查用户是否为资源所有者或管理员
        
        Args:
            resource_owner_id: 资源所有者ID
            user: 用户对象
            
        Returns:
            User: 用户对象
            
        Raises:
            HTTPException: 当用户不是所有者且不是管理员时抛出
        """
        # 要求用户存在且激活
        user = require_active_user(user)
        
        # 检查是否为所有者或管理员
        if user.id != resource_owner_id and not await self.is_admin(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改此资源"
            )
        return user
    
    async def check_moderator(
        self,
        user: Optional[User] = Depends(get_current_user)
    ) -> User:
        """检查用户是否为版主
        
        Args:
            user: 用户对象
            
        Returns:
            User: 用户对象
            
        Raises:
            HTTPException: 当用户不是版主时抛出
        """
        # 要求用户存在且激活
        user = require_active_user(user)
        
        # 检查是否为版主
        if not await self.is_moderator(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要版主权限"
            )
        return user

# 创建权限检查器实例
permission_checker = PermissionChecker()

# 导出便捷函数
check_permission = permission_checker.check_permission
check_owner = permission_checker.check_owner
check_moderator = permission_checker.check_moderator
is_admin = permission_checker.is_admin
is_moderator = permission_checker.is_moderator 