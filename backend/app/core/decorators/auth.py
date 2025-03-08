"""
认证相关装饰器

提供用于处理用户认证、授权和权限检查的装饰器：
- validate_token: 验证JWT令牌
- require_permissions: 检查用户权限
- require_roles: 检查用户角色
- owner_required: 检查资源所有权
"""

from fastapi import Request, HTTPException, status
from functools import wraps
from typing import List, Callable, TypeVar, Any
# 移除直接导入，改为函数内导入
# from ..auth import decode_token
from ...core.logging import get_logger
from ...core.permissions import Permission, Role

logger = get_logger(__name__)

T = TypeVar('T')

def validate_token(func: Callable[..., T]) -> Callable[..., T]:
    """
    验证JWT令牌的装饰器
    
    检查请求中的Authorization头部是否包含有效的JWT令牌。
    如果令牌无效或已过期，则返回401未授权错误。
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取request对象
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request and 'request' in kwargs:
            request = kwargs['request']
            
        if not request:
            raise ValueError("请求对象未找到，无法验证令牌")
        
        # 获取token
        authorization = request.headers.get('Authorization')
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少有效的身份验证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = authorization.split(' ')[1]
        
        # 验证token
        from ..auth import decode_token  # 延迟导入以避免循环引用
        token_data = decode_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌无效或已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 将用户信息存储在request.state中
        request.state.user = token_data
        
        return await func(*args, **kwargs)
    
    return wrapper

def require_permissions(permissions: List[Permission]):
    """
    权限检查装饰器
    
    检查当前用户是否拥有所需的所有权限。
    
    Args:
        permissions: 所需的权限列表
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当用户未登录或权限不足时抛出相应错误
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
                    
            if not request:
                # 尝试从kwargs中查找
                request = kwargs.get('request')
                
            if not request:
                logger.error(f"无法在 {func.__name__} 中找到Request对象")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器配置错误：无法访问请求对象"
                )
            
            # 检查用户是否已登录
            if not hasattr(request.state, "user") or not request.state.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录才能访问"
                )
            
            # 检查权限
            user_permissions = request.state.user.get("permissions", [])
            
            # 管理员拥有所有权限
            if "admin" in request.state.user.get("role", []):
                return await func(*args, **kwargs)
            
            # 检查是否有所需的所有权限
            for permission in permissions:
                if permission.value not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少所需权限: {permission.value}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def require_roles(roles: List[Role]):
    """
    角色检查装饰器
    
    检查当前用户是否拥有所需的任一角色。
    
    Args:
        roles: 所需的角色列表（满足其中之一即可）
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当用户未登录或角色不匹配时抛出相应错误
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
                    
            if not request:
                # 尝试从kwargs中查找
                request = kwargs.get('request')
                
            if not request:
                logger.error(f"无法在 {func.__name__} 中找到Request对象")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器配置错误：无法访问请求对象"
                )
            
            # 检查用户是否已登录
            if not hasattr(request.state, "user") or not request.state.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录才能访问"
                )
            
            # 检查角色
            user_role = request.state.user.get("role", "user")
            
            # 超级管理员拥有所有权限
            if user_role == "super_admin":
                return await func(*args, **kwargs)
            
            # 检查是否有所需的任一角色
            if not any(user_role == role.value for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join(role.value for role in roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def owner_required(get_owner_id_func: Callable):
    """
    资源所有者检查装饰器
    
    检查当前用户是否是资源的所有者。
    
    Args:
        get_owner_id_func: 一个函数，用于获取资源所有者的ID
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当用户未登录或不是资源所有者时抛出相应错误
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
                    
            if not request:
                # 尝试从kwargs中查找
                request = kwargs.get('request')
                
            if not request:
                logger.error(f"无法在 {func.__name__} 中找到Request对象")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器配置错误：无法访问请求对象"
                )
            
            # 检查用户是否已登录
            if not hasattr(request.state, "user") or not request.state.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录才能访问"
                )
            
            # 获取当前用户ID
            user_id = request.state.user.get("id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的用户信息"
                )
            
            # 管理员可以访问任何资源
            user_role = request.state.user.get("role", "user")
            if user_role in ["admin", "super_admin"]:
                return await func(*args, **kwargs)
            
            # 获取资源所有者ID
            try:
                owner_id = await get_owner_id_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"获取资源所有者ID失败: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法确定资源所有权"
                )
            
            # 检查所有权
            if str(user_id) != str(owner_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此资源"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator 