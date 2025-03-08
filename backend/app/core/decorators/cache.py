"""
缓存相关装饰器

提供函数结果缓存的装饰器：
- memo: 基本内存缓存装饰器
- async_memo: 异步函数的内存缓存装饰器
- timed_memo: 带过期时间的内存缓存装饰器
- typed_memo: 类型敏感的内存缓存装饰器
"""

from functools import wraps
from typing import TypeVar, Callable, Dict, Any, Optional, Tuple, Type
from typing import TypeVar, Callable, Dict, Any, Optional, List, Tuple, Type
import time
import hashlib
from ...core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
V = TypeVar('V')

# 全局缓存存储
_memo_cache: Dict[str, Dict[str, Any]] = {}

def _get_func_name(func: Callable) -> str:
    """获取函数的完整名称，包括模块"""
    module = func.__module__
    name = func.__qualname__
    return f"{module}.{name}"

def _build_key(func: Callable, args: Tuple, kwargs: Dict[str, Any]) -> str:
    """构建缓存键"""
    # 将位置参数和关键字参数序列化为字符串
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # 使用函数名和参数创建唯一的键
    func_name = _get_func_name(func)
    key = f"{func_name}({', '.join(key_parts)})"
    
    # 对长键进行哈希处理
    if len(key) > 250:
        key = hashlib.md5(key.encode()).hexdigest()
    
    return key

def _clear_memo_cache(namespace: Optional[str] = None) -> int:
    """清理内存缓存
    
    Args:
        namespace: 可选的命名空间，如果提供，只清理该命名空间下的缓存
        
    Returns:
        int: 清理的缓存项数量
    """
    global _memo_cache
    count = 0
    
    if namespace:
        if namespace in _memo_cache:
            count = len(_memo_cache[namespace])
            _memo_cache[namespace] = {}
    else:
        count = sum(len(cache) for cache in _memo_cache.values())
        _memo_cache = {}
    
    return count

def memo(func: Callable[..., T]) -> Callable[..., T]:
    """
    基本内存缓存装饰器
    
    缓存函数的返回值，相同的参数调用只执行一次函数。
    
    警告：此装饰器没有过期机制，缓存会一直保存在内存中，
    适用于返回值很少变化的纯函数。
    
    Args:
        func: 要缓存的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    namespace = _get_func_name(func)
    
    if namespace not in _memo_cache:
        _memo_cache[namespace] = {}
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # 构建缓存键
        key = _build_key(func, args, kwargs)
        
        # 检查缓存
        if key in _memo_cache[namespace]:
            logger.debug(f"缓存命中: {namespace}.{key}")
            return _memo_cache[namespace][key]
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 缓存结果
        _memo_cache[namespace][key] = result
        logger.debug(f"缓存设置: {namespace}.{key}")
        
        return result
    
    # 添加清理方法
    wrapper.clear_cache = lambda: _clear_memo_cache(namespace)
    
    return wrapper

def async_memo(func: Callable[..., T]) -> Callable[..., T]:
    """
    异步函数的内存缓存装饰器
    
    缓存异步函数的返回值，相同的参数调用只执行一次函数。
    
    警告：此装饰器没有过期机制，缓存会一直保存在内存中，
    适用于返回值很少变化的纯函数。
    
    Args:
        func: 要缓存的异步函数
        
    Returns:
        Callable: 装饰后的异步函数
    """
    namespace = _get_func_name(func)
    
    if namespace not in _memo_cache:
        _memo_cache[namespace] = {}
    
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # 构建缓存键
        key = _build_key(func, args, kwargs)
        
        # 检查缓存
        if key in _memo_cache[namespace]:
            logger.debug(f"缓存命中: {namespace}.{key}")
            return _memo_cache[namespace][key]
        
        # 执行函数
        result = await func(*args, **kwargs)
        
        # 缓存结果
        _memo_cache[namespace][key] = result
        logger.debug(f"缓存设置: {namespace}.{key}")
        
        return result
    
    # 添加清理方法
    wrapper.clear_cache = lambda: _clear_memo_cache(namespace)
    
    return wrapper

def timed_memo(expire: int = 60):
    """
    带过期时间的内存缓存装饰器
    
    缓存函数的返回值，并在指定时间后过期。
    
    Args:
        expire: 缓存过期时间（秒），默认60秒
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        namespace = _get_func_name(func)
        
        if namespace not in _memo_cache:
            _memo_cache[namespace] = {}
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # 构建缓存键
            key = _build_key(func, args, kwargs)
            
            # 检查缓存
            now = time.time()
            if key in _memo_cache[namespace]:
                cache_data = _memo_cache[namespace][key]
                if cache_data["expires_at"] > now:
                    logger.debug(f"缓存命中: {namespace}.{key}")
                    return cache_data["value"]
                else:
                    # 删除过期缓存
                    del _memo_cache[namespace][key]
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            _memo_cache[namespace][key] = {
                "value": result,
                "expires_at": now + expire
            }
            logger.debug(f"缓存设置: {namespace}.{key}, 过期时间: {expire}秒")
            
            return result
        
        # 添加清理方法
        wrapper.clear_cache = lambda: _clear_memo_cache(namespace)
        
        return wrapper
    
    return decorator

def typed_memo(func: Callable[..., T]) -> Callable[..., T]:
    """
    类型敏感的内存缓存装饰器
    
    缓存函数的返回值，考虑参数的类型而不仅仅是值。
    
    例如，memo中 1 和 "1" 可能会得到相同的缓存键，
    而typed_memo会将它们视为不同的键。
    
    Args:
        func: 要缓存的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    namespace = _get_func_name(func)
    
    if namespace not in _memo_cache:
        _memo_cache[namespace] = {}
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # 构建包含类型信息的缓存键
        typed_args = [(type(arg).__name__, arg) for arg in args]
        typed_kwargs = {k: (type(v).__name__, v) for k, v in kwargs.items()}
        
        # 使用类型信息创建键
        key = _build_key(func, typed_args, typed_kwargs)
        
        # 检查缓存
        if key in _memo_cache[namespace]:
            logger.debug(f"缓存命中: {namespace}.{key}")
            return _memo_cache[namespace][key]
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 缓存结果
        _memo_cache[namespace][key] = result
        logger.debug(f"缓存设置: {namespace}.{key}")
        
        return result
    
    # 添加清理方法
    wrapper.clear_cache = lambda: _clear_memo_cache(namespace)
    
    return wrapper 