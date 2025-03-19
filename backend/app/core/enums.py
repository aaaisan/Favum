"""
系统枚举定义

此模块定义了系统中使用的各种枚举类型，如角色、权限等。
"""

from enum import Enum

class Role(str, Enum):
    """系统角色定义"""
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    
    def __str__(self) -> str:
        return self.value

class Permission(str, Enum):
    """系统权限定义"""
    # 帖子相关权限
    CREATE_POST = "create_post"
    EDIT_POST = "edit_post"
    DELETE_POST = "delete_post"
    HIDE_POST = "hide_post"
    
    # 评论相关权限
    CREATE_COMMENT = "create_comment"
    EDIT_COMMENT = "edit_comment"
    DELETE_COMMENT = "delete_comment"
    
    # 用户相关权限
    EDIT_PROFILE = "edit_profile"
    VIEW_USERS = "view_users"
    
    # 管理权限
    MANAGE_USERS = "manage_users"
    MANAGE_CONTENT = "manage_content"
    MANAGE_SECTIONS = "manage_sections"
    MANAGE_SYSTEM = "manage_system" 

class VoteType(str, Enum):
    """点赞类型枚举"""
    UPVOTE = "upvote"    # 点赞
    DOWNVOTE = "downvote"  # 反对