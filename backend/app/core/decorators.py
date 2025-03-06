"""
装饰器模块

提供一组功能强大的装饰器，用于增强API端点和服务方法的功能：

认证与授权：
- validate_token: Token验证
- require_permissions: 权限检查
- require_roles: 角色检查
- owner_required: 资源所有者验证

性能与可靠性：
- cache: 响应缓存
- rate_limit: 请求限流
- retry: 自动重试
- log_execution_time: 执行时间记录
- log_exception: 异常日志记录

错误处理：
- handle_exceptions: 统一异常处理

内存缓存：
- memo: 基本内存缓存装饰器
- async_memo: 异步函数的内存缓存装饰器
- timed_memo: 带过期时间的内存缓存装饰器
- typed_memo: 类型敏感的内存缓存装饰器

上下文管理器：
- redis_pipeline: Redis管道操作上下文
- profiling: 性能分析上下文
- transaction: 数据库事务上下文
- error_boundary: 错误处理边界上下文
- request_context: 请求上下文

所有装饰器和上下文管理器都支持异步函数，并提供完整的类型提示。

注意：此模块导入并重新导出了单独装饰器文件中的装饰器，
以保持向后兼容性。建议在新代码中直接从专用模块导入。
"""

# 导入认证相关装饰器
from .auth_decorators import (
    validate_token,
    require_permissions,
    require_roles,
    owner_required
)

# 导入性能相关装饰器
from .performance_decorators import (
    cache,
    rate_limit,
    log_execution_time
)

# 导入错误处理相关装饰器
from .error_decorators import (
    handle_exceptions,
    retry
)

# 导入内存缓存装饰器
from .cache_decorators import (
    memo,
    async_memo,
    timed_memo,
    typed_memo
)

# 导入上下文管理器
from .context_managers import (
    redis_pipeline,
    profiling,
    transaction,
    error_boundary,
    request_context
)

# 导入日志装饰器 - 从 utils 移至 core
from .logging_decorators import (
    log_exception
)

from fastapi import HTTPException, Request
from functools import wraps
from typing import Callable, Optional, Any, Dict, TypeVar, Type, Union
from datetime import timedelta
import inspect
import logging
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from .cache import RateLimiter
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

def endpoint_rate_limit(
    limit: int = 60,
    window: int = 60,
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    端点级别的速率限制装饰器
    
    限制特定API端点的请求频率，使用Redis实现分布式限流。
    
    Args:
        limit: 时间窗口内允许的最大请求数，默认60
        window: 时间窗口大小(秒)，默认60秒
        key_func: 自定义缓存键生成函数，可根据请求生成唯一的限流键
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # 提取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 在关键字参数中查找
                request = kwargs.get('request')
            
            if not request:
                logger.warning(f"无法在 {func.__name__} 中找到Request对象，跳过限流检查")
                return await func(*args, **kwargs)
            
            # 生成限流键
            client_id = request.client.host
            
            # 如果有用户信息，使用用户ID
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.get("id")
                if user_id:
                    client_id = f"user:{user_id}"
            
            # 使用自定义键生成函数或默认方式
            if key_func:
                rate_limit_key = key_func(request)
            else:
                # 默认使用函数名称和客户端ID组合
                rate_limit_key = f"rate_limit:{func.__module__}.{func.__name__}:{client_id}"
            
            # 使用RateLimiter进行限流检查
            is_allowed = await RateLimiter.is_allowed(
                "endpoint",  # 使用endpoint作为前缀
                rate_limit_key,
                limit,
                timedelta(seconds=window)
            )
            
            if not is_allowed:
                logger.warning(
                    f"端点限流触发: {client_id} - {request.method} {request.url.path} - "
                    f"函数: {func.__name__}"
                )
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求太频繁，请稍后再试"
                )
            
            # 通过限流检查，执行原始函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# 为保持向后兼容性，重新导出所有装饰器和上下文管理器
__all__ = [
    # 认证相关
    'validate_token',
    'require_permissions',
    'require_roles',
    'owner_required',
    
    # 性能相关
    'cache',
    'rate_limit',
    'log_execution_time',
    
    # 错误处理相关
    'handle_exceptions',
    'retry',
    
    # 内存缓存相关
    'memo',
    'async_memo',
    'timed_memo',
    'typed_memo',
    
    # 日志相关
    'log_exception',
    
    # 上下文管理器
    'redis_pipeline',
    'profiling',
    'transaction',
    'error_boundary',
    'request_context'
] 