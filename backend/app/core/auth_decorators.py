"""
认证与授权装饰器模块

提供用于API认证和授权的装饰器：
- validate_token: Token验证
- require_permissions: 权限检查
- require_roles: 角色检查
- owner_required: 资源所有者验证

所有装饰器都支持异步函数，并提供完整的类型提示。
"""

from functools import wraps
from typing import Any, Callable, List, Optional, Union
from datetime import datetime

from fastapi import HTTPException, Request, status
from jose import JWTError

from .logging import get_logger
from .config import settings
from .permissions import Permission, Role, get_role_permissions

logger = get_logger(__name__)

def validate_token(func: Callable) -> Callable:
    """
    Token验证装饰器
    
    验证请求头中的JWT令牌。
    
    Args:
        func: 要装饰的函数
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当令牌无效或缺失时抛出401错误
        
    Notes:
        - 从Authorization头获取Bearer令牌
        - 验证令牌签名和过期时间
        - 将用户信息存储在request.state.user中
        
    Example:
        @validate_token
        async def protected_route():
            ...
    """
    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="未提供认证Token"
                )
            
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="无效的Token格式"
                )
            
            token = auth_header.split(" ")[1]
            try:
                # 验证token
                payload = request.app.state.jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                
                # 验证token是否过期
                exp = payload.get("exp")
                if not exp or datetime.fromtimestamp(exp) < datetime.now():
                    raise HTTPException(
                        status_code=401,
                        detail="Token已过期"
                    )
                
                # 验证token是否被撤销
                # 使用异步方式调用Redis
                is_revoked = await request.app.state.redis.sismember("revoked_tokens", token)
                if is_revoked:
                    raise HTTPException(
                        status_code=401,
                        detail="Token已被撤销"
                    )
                
                request.state.user = payload
                request.state.token = token  # 保存token以便后续使用
                
            except JWTError as e:
                logger.error(f"Token解析失败: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail="无效的Token"
                )
            
            return await func(request, *args, **kwargs)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token验证失败: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="认证失败"
            )
    return wrapper

def require_permissions(
    permissions: Union[Permission, List[Permission]],
    require_all: bool = True
):
    """权限检查装饰器
    
    检查当前请求的用户是否拥有所需的权限。
    
    Args:
        permissions: 单个权限或权限列表
        require_all: 是否要求拥有所有列出的权限（True）或只需任意一个（False）
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当用户没有所需权限时抛出403错误
        
    Example:
        @require_permissions(Permission.EDIT_POST)
        async def update_content():
            ...
        
        @require_permissions([Permission.EDIT_POST, Permission.DELETE_POST])
        async def manage_content():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # 获取当前用户
            user = request.state.user
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="凭证无效",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 转换单个权限为列表
            perm_list = [permissions] if isinstance(permissions, Permission) else permissions
            
            # 检查用户权限
            if require_all and not all(p in user.get("permissions", []) for p in perm_list):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足，无法执行此操作"
                )
            elif not require_all and not any(p in user.get("permissions", []) for p in perm_list):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足，无法执行此操作"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_roles(roles: Union[Role, List[Role]]):
    """
    角色验证装饰器
    
    检查当前用户是否具有指定的角色。
    
    Args:
        roles: 单个角色或角色列表
        
    Returns:
        Callable: 装饰器函数
        
    Raises:
        HTTPException: 当用户角色不匹配时抛出403错误
        ValueError: 当提供的角色无效时抛出
        
    Notes:
        - 支持检查单个或多个角色
        - 只要匹配其中一个角色即可通过
        - 自动验证提供的角色是否为有效的Role枚举成员
        
    Example:
        ```python
        @require_roles([Role.ADMIN, Role.SUPER_ADMIN])
        async def admin_operation():
            ...
        ```
    """
    # 验证提供的角色是否有效
    valid_roles = list(Role)
    
    if isinstance(roles, Role):
        roles = [roles]
    
    # 验证每个角色是否有效
    for role in roles:
        if role not in valid_roles:
            raise ValueError(f"无效的角色值: {role}，有效的角色有: {[r.name for r in valid_roles]}")
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=401,
                    detail="需要认证"
                )
            
            user_role = request.state.user.get("role")
            if not user_role or user_role not in [r.value for r in roles]:
                allowed_roles = ", ".join([r.name for r in roles])
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足，需要以下角色之一: {allowed_roles}"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def owner_required(get_owner_id):
    """
    资源所有者验证装饰器
    
    验证当前用户是否为资源的所有者。
    
    Args:
        get_owner_id: 从请求参数中获取资源所有者ID的函数
        
    Returns:
        装饰器函数
        
    Raises:
        HTTPException: 当用户不是资源所有者时抛出403错误
        
    Notes:
        - 依赖validate_token装饰器
        - 支持自定义所有者ID提取逻辑
        - 可与其他权限装饰器组合使用
        
    Example:
        @owner_required(lambda params: params.get("user_id"))
        async def update_profile():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=401,
                    detail="需要认证"
                )
            
            owner_id = get_owner_id(kwargs)
            if str(owner_id) != str(request.state.user.get("id")):
                raise HTTPException(
                    status_code=403,
                    detail="没有权限访问此资源"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator 