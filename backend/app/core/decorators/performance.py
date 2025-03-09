"""
性能相关装饰器

提供性能优化和控制的装饰器：
- rate_limit: 请求速率限制
- cache: 响应缓存
- endpoint_rate_limit: 端点级请求限流
"""

from fastapi import Request, HTTPException, Depends
# from fastapi import Request, HTTPException, Response, Depends
from functools import wraps
from typing import TypeVar, Callable, Dict, Any, Optional, List
# from typing import TypeVar, Callable, Dict, Any, Optional, Union, List
import time
import hashlib
import json
from datetime import timedelta
# from datetime import datetime, timedelta
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from ...core.logging import get_logger
from ...core.cache import RateLimiter

logger = get_logger(__name__)

T = TypeVar('T')

# 简单内存缓存（仅用于开发/测试）
_CACHE: Dict[str, Dict[str, Any]] = {}

def rate_limit(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    速率限制装饰器
    
    限制API请求频率。
    
    Args:
        limit: 请求限制数，默认为60
        window: 时间窗口（秒），默认为60
        key_func: 自定义键生成函数，用于区分不同请求者
        
    Returns:
        Callable: 装饰器函数
    """
    # 使用默认值
    _limit = limit if limit is not None else 60
    _window = window if window is not None else 60
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 尝试从关键字参数获取
                request = kwargs.get('request')
            
            if not request:
                logger.warning(f"无法获取请求对象，跳过速率限制: {func.__name__}")
                return await func(*args, **kwargs)
            
            # 生成限流键
            client_id = request.client.host
            
            # 如果有用户会话，使用用户ID
            if hasattr(request.state, 'user') and request.state.user:
                user_id = request.state.user.get('id')
                if user_id:
                    client_id = f"user:{user_id}"
            
            # 使用自定义键函数或默认键
            if key_func:
                cache_key = key_func(request)
            else:
                path = request.url.path
                cache_key = f"rate_limit:{func.__name__}:{client_id}:{path}"
            
            # 使用Redis实现的分布式限流器
            is_allowed = await RateLimiter.is_allowed(
                "api",
                cache_key,
                _limit,
                timedelta(seconds=_window)
            )
            
            if not is_allowed:
                logger.warning(f"速率限制触发: {client_id}, 函数: {func.__name__}")
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请在{_window}秒后重试"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def cache(
    expire: int = 60,
    key_prefix: Optional[str] = None,
    include_query_params: bool = True,
    include_user_id: bool = False
):
    """
    响应缓存装饰器
    
    缓存API响应以提高性能。
    
    Args:
        expire: 缓存过期时间（秒），默认60秒
        key_prefix: 缓存键前缀，默认使用函数名
        include_query_params: 是否在缓存键中包含查询参数，默认True
        include_user_id: 是否在缓存键中包含用户ID，默认False
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func):
        # 使用函数名作为默认前缀
        prefix = key_prefix or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 尝试从关键字参数获取
                request = kwargs.get('request')
            
            if not request:
                logger.warning(f"无法获取请求对象，跳过缓存: {func.__name__}")
                return await func(*args, **kwargs)
            
            # 只缓存GET请求
            if request.method != "GET":
                return await func(*args, **kwargs)
            
            # 构建缓存键
            key_parts = [prefix, request.url.path]
            
            # 包含查询参数
            if include_query_params and request.query_params:
                # 将查询参数按字母顺序排序
                sorted_params = dict(sorted(request.query_params.items()))
                key_parts.append(json.dumps(sorted_params))
            
            # 包含用户ID
            if include_user_id and hasattr(request.state, 'user') and request.state.user:
                user_id = request.state.user.get('id')
                if user_id:
                    key_parts.append(f"user:{user_id}")
            
            # 生成最终缓存键
            cache_key = ":".join(key_parts)
            if len(cache_key) > 250:
                # 如果键太长，使用哈希
                cache_key = f"{prefix}:{hashlib.md5(cache_key.encode()).hexdigest()}"
            
            # 尝试从缓存获取
            now = time.time()
            
            if cache_key in _CACHE:
                cache_data = _CACHE[cache_key]
                if cache_data['expires_at'] > now:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cache_data['data']
                else:
                    # 清理过期项
                    del _CACHE[cache_key]
            
            # 缓存未命中，执行函数
            response = await func(*args, **kwargs)
            
            # 缓存响应
            _CACHE[cache_key] = {
                'data': response,
                'expires_at': now + expire
            }
            
            logger.debug(f"缓存设置: {cache_key}, 过期时间: {expire}秒")
            
            # 定期清理缓存
            if len(_CACHE) > 1000:
                _clean_cache()
            
            return response
        
        return wrapper
    
    return decorator

def _clean_cache():
    """清理过期的缓存项"""
    now = time.time()
    expired_keys = [k for k, v in _CACHE.items() if v['expires_at'] <= now]
    
    for key in expired_keys:
        del _CACHE[key]
    
    logger.debug(f"已清理 {len(expired_keys)} 个过期缓存项")

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