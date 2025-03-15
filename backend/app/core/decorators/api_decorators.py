"""
API装饰器工具模块

提供用于API端点的工具函数和装饰器组合，简化重复的装饰器模式。
主要功能：
- 装饰器组合：将多个常用装饰器组合为一个函数
- 权限控制助手：简化权限验证
- 错误处理助手：统一的异常处理

通过使用这些工具，可以简化端点代码，避免重复的装饰器堆叠。
"""

import logging
from typing import Optional, Any
from typing import List, Optional, Any
from functools import wraps

from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from ..enums import Role, Permission
from . import (
    handle_exceptions,
    rate_limit,
    cache,
    validate_token,
    log_execution_time,
    require_permissions,
    require_roles,
    owner_required
)

def admin_endpoint(
    *exceptions: Any,
    rate_limit_count: Optional[int] = None,
    cache_ttl: Optional[int] = None,
    custom_message: Optional[str] = None
):
    """
    管理员端点装饰器组合
    
    结合异常处理、令牌验证、角色检查和执行时间日志的装饰器组合。
    专为管理员权限的端点设计。
    
    Args:
        *exceptions: 要捕获的异常类型，默认为SQLAlchemyError
        rate_limit_count: 速率限制计数，如果提供则添加速率限制
        cache_ttl: 缓存过期时间（秒），如果提供则添加缓存
        custom_message: 自定义错误消息，默认使用"操作失败"
        
    Returns:
        组合多个装饰器的装饰器函数
        
    Example:
        @admin_endpoint(rate_limit_count=10)
        async def admin_function(request: Request):
            ...
    """
    _exceptions = exceptions if exceptions else (SQLAlchemyError,)
    _message = custom_message if custom_message else "操作失败"
    
    def decorator(func):
        # 应用基本装饰器：异常处理、令牌验证和角色检查
        _decorated = handle_exceptions(
            *_exceptions, 
            status_code=500, 
            message=_message, 
            include_details=True
        )(
            validate_token(
                require_roles([Role.ADMIN, Role.SUPER_ADMIN])(
                    log_execution_time(
                        level=logging.INFO, 
                        message="{function_name} 执行完成，用时 {execution_time:.3f}秒"
                    )(func)
                )
            )
        )
        
        # 可选添加速率限制
        if rate_limit_count:
            _decorated = rate_limit(limit=rate_limit_count, window=3600)(_decorated)
            
        # 可选添加缓存
        if cache_ttl:
            _decorated = cache(expire=cache_ttl, include_query_params=True)(_decorated)
            
        return _decorated
    
    return decorator

def moderator_endpoint(
    *exceptions: Any,
    rate_limit_count: Optional[int] = None,
    cache_ttl: Optional[int] = None,
    custom_message: Optional[str] = None
):
    """
    版主端点装饰器组合
    
    结合异常处理、令牌验证、角色检查和执行时间日志的装饰器组合。
    专为版主权限的端点设计，包括版主和管理员角色。
    
    Args:
        *exceptions: 要捕获的异常类型，默认为SQLAlchemyError
        rate_limit_count: 速率限制计数，如果提供则添加速率限制
        cache_ttl: 缓存过期时间（秒），如果提供则添加缓存
        custom_message: 自定义错误消息，默认使用"操作失败"
        
    Returns:
        组合多个装饰器的装饰器函数
    """
    _exceptions = exceptions if exceptions else (SQLAlchemyError,)
    _message = custom_message if custom_message else "操作失败"
    
    def decorator(func):
        # 应用基本装饰器：异常处理、令牌验证和角色检查
        _decorated = handle_exceptions(
            *_exceptions, 
            status_code=500, 
            message=_message, 
            include_details=True
        )(
            validate_token(
                require_roles([Role.MODERATOR, Role.ADMIN, Role.SUPER_ADMIN])(
                    log_execution_time(
                        level=logging.INFO, 
                        message="{function_name} 执行完成，用时 {execution_time:.3f}秒"
                    )(func)
                )
            )
        )
        
        # 可选添加速率限制
        if rate_limit_count:
            _decorated = rate_limit(limit=rate_limit_count, window=3600)(_decorated)
            
        # 可选添加缓存
        if cache_ttl:
            _decorated = cache(expire=cache_ttl, include_query_params=True)(_decorated)
            
        return _decorated
    
    return decorator

def public_endpoint(
    *exceptions: Any,
    rate_limit_count: Optional[int] = None,
    cache_ttl: Optional[int] = None,
    auth_required: bool = False,
    custom_message: Optional[str] = None
):
    """
    公共端点装饰器组合
    
    结合异常处理、可选令牌验证和执行时间日志的装饰器组合。
    适用于公共访问端点，可选是否需要身份验证。
    
    Args:
        *exceptions: 要捕获的异常类型，默认为SQLAlchemyError
        rate_limit_count: 速率限制计数，如果提供则添加速率限制
        cache_ttl: 缓存过期时间（秒），如果提供则添加缓存
        auth_required: 是否需要认证，默认为False
        custom_message: 自定义错误消息，默认使用"操作失败"
        
    Returns:
        组合多个装饰器的装饰器函数
    """
    _exceptions = exceptions if exceptions else (SQLAlchemyError,)
    _message = custom_message if custom_message else "操作失败"
    
    def decorator(func):
        # 先保存原始函数引用
        original_func = func
        decorated_func = func
        
        # 1. 首先添加令牌验证（如果需要）
        # 这必须是第一个应用的装饰器，因为其他装饰器可能依赖request.state.user
        if auth_required:
            decorated_func = validate_token(decorated_func)
        
        # 2. 应用异常处理和日志记录
        decorated_func = handle_exceptions(
            *_exceptions, 
            status_code=500, 
            message=_message, 
            include_details=True
        )(
            log_execution_time(
                level=logging.INFO, 
                message="{function_name} 执行完成，用时 {execution_time:.3f}秒"
            )(decorated_func)
        )
        
        # 3. 可选添加速率限制
        if rate_limit_count:
            decorated_func = rate_limit(limit=rate_limit_count, window=3600)(decorated_func)
            
        # 4. 可选添加缓存
        if cache_ttl:
            decorated_func = cache(expire=cache_ttl, include_query_params=True)(decorated_func)
            
        return decorated_func
    
    return decorator

def owner_endpoint(
    owner_param_name: str = None,
    *exceptions: Any,
    rate_limit_count: Optional[int] = None,
    custom_message: Optional[str] = None,
    allow_moderator: bool = True,
    resource_owner_lookup_func: Optional[callable] = None
):
    """
    资源所有者端点装饰器组合
    
    结合异常处理、令牌验证、所有者检查和执行时间日志的装饰器组合。
    专为资源所有者权限的端点设计，可选允许版主和管理员访问。
    
    Args:
        owner_param_name: 包含资源所有者ID的参数名称，与resource_owner_lookup_func二选一
        *exceptions: 要捕获的异常类型，默认为SQLAlchemyError
        rate_limit_count: 速率限制计数，如果提供则添加速率限制
        custom_message: 自定义错误消息，默认使用"操作失败"
        allow_moderator: 是否允许版主和管理员访问，默认为True
        resource_owner_lookup_func: 资源所有者查找函数，用于从资源ID获取所有者ID
        
    Returns:
        组合多个装饰器的装饰器函数
    """
    if owner_param_name is None and resource_owner_lookup_func is None:
        raise ValueError("owner_param_name 和 resource_owner_lookup_func 必须至少提供一个")
        
    _exceptions = exceptions if exceptions else (SQLAlchemyError,)
    _message = custom_message if custom_message else "操作失败"
    
    def decorator(func):
        # 创建一个内部函数，封装owner_getter逻辑
        if allow_moderator:
            # 如果允许版主访问，使用自定义装饰器
            @wraps(func)
            async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
                if not hasattr(request.state, "user"):
                    raise HTTPException(
                        status_code=401,
                        detail="需要认证"
                    )
                
                user_role = request.state.user.get("role", "user")
                user_id = request.state.user.get("id")
                
                # 如果是管理员或版主，直接允许访问
                if user_role in ["admin", "super_admin", "moderator"]:
                    return await func(request, *args, **kwargs)
                
                # 根据提供的方法获取资源所有者ID
                owner_id = None
                
                if resource_owner_lookup_func:
                    # 通过回调函数获取所有者ID
                    try:
                        owner_id = await resource_owner_lookup_func(*args, **kwargs)
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"无法确定资源所有权: {str(e)}"
                        )
                else:
                    # 直接从参数获取所有者ID
                    owner_id = kwargs.get(owner_param_name)
                    if owner_id is None:
                        raise HTTPException(
                            status_code=500,
                            detail=f"参数 {owner_param_name} 未找到"
                        )
                
                if str(owner_id) != str(user_id):
                    raise HTTPException(
                        status_code=403,
                        detail="没有权限访问此资源"
                    )
                
                return await func(request, *args, **kwargs)
            
            # 应用其他装饰器
            _decorated = handle_exceptions(
                *_exceptions, 
                status_code=500, 
                message=_message, 
                include_details=True
            )(
                validate_token(
                    log_execution_time(
                        level=logging.INFO, 
                        message="{function_name} 执行完成，用时 {execution_time:.3f}秒"
                    )(wrapper)
                )
            )
        else:
            # 如果不允许版主访问，使用修改后的逻辑
            @wraps(func)
            async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
                if not hasattr(request.state, "user"):
                    raise HTTPException(
                        status_code=401,
                        detail="需要认证"
                    )
                
                user_role = request.state.user.get("role", "user")
                user_id = request.state.user.get("id")
                
                # 如果是超级管理员或管理员，直接允许访问
                if user_role in ["admin", "super_admin"]:
                    return await func(request, *args, **kwargs)
                
                # 根据提供的方法获取资源所有者ID
                owner_id = None
                
                if resource_owner_lookup_func:
                    # 通过回调函数获取所有者ID
                    try:
                        owner_id = await resource_owner_lookup_func(*args, **kwargs)
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"无法确定资源所有权: {str(e)}"
                        )
                else:
                    # 直接从参数获取所有者ID
                    owner_id = kwargs.get(owner_param_name)
                    if owner_id is None:
                        raise HTTPException(
                            status_code=500,
                            detail=f"参数 {owner_param_name} 未找到"
                        )
                
                if str(owner_id) != str(user_id):
                    raise HTTPException(
                        status_code=403,
                        detail="没有权限访问此资源"
                    )
                
                return await func(request, *args, **kwargs)
                
            # 应用其他装饰器
            _decorated = handle_exceptions(
                *_exceptions, 
                status_code=500, 
                message=_message, 
                include_details=True
            )(
                validate_token(
                    log_execution_time(
                        level=logging.INFO, 
                        message="{function_name} 执行完成，用时 {execution_time:.3f}秒"
                    )(wrapper)
                )
            )
        
        # 可选添加速率限制
        if rate_limit_count:
            _decorated = rate_limit(limit=rate_limit_count, window=3600)(_decorated)
            
        return _decorated
    
    return decorator 