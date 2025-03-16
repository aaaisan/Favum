"""依赖注入模块

此模块提供了FastAPI应用中使用的各种依赖注入函数，
包括认证、权限控制、资源访问、分页等功能。

提供FastAPI依赖注入函数，用于获取各种服务实例和资源。
这些函数被用作FastAPI的依赖项，以实现依赖注入模式。
"""

# 导出认证相关依赖
from .auth import (
    get_current_user,
    require_user,
    require_active_user
)

# 导出权限相关依赖
from .permission import (
    require_admin,
    require_moderator,
    check_post_ownership,
    is_section_moderator
)

# 导出分页和过滤相关依赖
from .pagination import (
    get_pagination_params,
    get_sorting_params,
    get_post_filters,
    SortOrder
)

# 导出资源访问相关依赖
from .resources import (
    get_post_or_404,
    get_section_or_404,
    get_category_or_404,
    get_comment_or_404,
    validate_post_access,
    get_db_from_request
)

# 导出限流相关依赖 (替换了旧的rate_limit模块)
from .limit import (
    rate_limit,
    ip_rate_limit
)

# 导出缓存相关依赖
from .cache import (
    get_cached_response,
    set_cached_response
)

# 导出审计日志相关依赖
from .audit import (
    audit_log,
    AuditLogMarker
)

from ..services.user_service import UserService
from ..services.post_service import PostService
from ..services.favorite_service import FavoriteService
from ..services.comment_service import CommentService

def get_user_service() -> UserService:
    """获取用户服务实例
    
    用于FastAPI依赖注入系统
    
    Returns:
        UserService: 用户服务实例
    """
    return UserService()

def get_post_service() -> PostService:
    """获取帖子服务实例
    
    用于FastAPI依赖注入系统
    
    Returns:
        PostService: 帖子服务实例
    """
    return PostService()

def get_favorite_service() -> FavoriteService:
    """获取收藏服务实例
    
    用于FastAPI依赖注入系统
    
    Returns:
        FavoriteService: 收藏服务实例
    """
    return FavoriteService()

def get_comment_service() -> CommentService:
    """获取评论服务实例
    
    用于FastAPI依赖注入系统
    
    Returns:
        CommentService: 评论服务实例
    """
    return CommentService()

__all__ = [
    # 认证
    'get_current_user', 'require_user', 'require_active_user',
    
    # 权限
    'require_admin', 'require_moderator', 'check_post_ownership', 'is_section_moderator',
    
    # 分页
    'get_pagination_params', 'get_sorting_params', 'get_post_filters', 'SortOrder',
    
    # 资源
    'get_post_or_404', 'get_section_or_404', 'get_category_or_404', 'get_comment_or_404',
    'validate_post_access', 'get_db_from_request',
    
    # 限流
    'rate_limit', 'ip_rate_limit',
    
    # 缓存
    'get_cached_response', 'set_cached_response',
    
    # 审计
    'audit_log', 'AuditLogMarker',
    
    # 服务
    'get_user_service',
    'get_post_service',
    'get_favorite_service',
    'get_comment_service'
] 