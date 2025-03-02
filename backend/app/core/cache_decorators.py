"""
缓存装饰器模块

提供基于Python标准库functools的内存缓存装饰器，用于优化重复计算：
- memo: 基本内存缓存装饰器
- async_memo: 异步函数的内存缓存装饰器
- timed_memo: 带过期时间的内存缓存装饰器
- typed_memo: 类型敏感的内存缓存装饰器

所有装饰器都提供完整的类型提示和文档。
"""

from __future__ import annotations
import functools
import time
import inspect
import asyncio
from typing import Any, Dict, Optional, Tuple, TypeVar, cast

F = TypeVar('F')

def memo(maxsize: int = 128, typed: bool = False):
    """
    内存缓存装饰器
    
    使用functools.lru_cache缓存函数结果，避免重复计算。
    
    Args:
        maxsize: 缓存的最大条目数，设为None表示无限制
        typed: 是否区分参数类型（例如区分int和float）
        
    Returns:
        装饰器函数
        
    Notes:
        - 适用于计算密集型且频繁调用的函数
        - 参数必须是可哈希的类型
        - 已提供缓存统计信息访问
        
    Example:
        ```python
        @memo(maxsize=100)
        def expensive_computation(x, y):
            # 复杂计算
            return result
            
        # 访问缓存统计
        print(expensive_computation.cache_info())
        
        # 清除缓存
        expensive_computation.cache_clear()
        ```
    """
    return functools.lru_cache(maxsize=maxsize, typed=typed)

def _make_key(args: Tuple, kwargs: Dict[str, Any], typed: bool) -> Tuple:
    """
    创建缓存键
    
    Args:
        args: 位置参数
        kwargs: 关键字参数
        typed: 是否区分类型
        
    Returns:
        缓存键元组
    """
    key_parts = list(args)
    
    if kwargs:
        sorted_items = sorted(kwargs.items())
        if typed:
            key_parts.extend([f"{k}:{type(v).__name__}:{v}" for k, v in sorted_items])
        else:
            key_parts.extend([f"{k}:{v}" for k, v in sorted_items])
            
    return tuple(key_parts)

def async_memo(maxsize: int = 128, typed: bool = False):
    """
    异步函数的内存缓存装饰器
    
    对异步函数的结果进行缓存，避免重复计算。
    
    Args:
        maxsize: 缓存的最大条目数，设为None表示无限制
        typed: 是否区分参数类型
        
    Returns:
        装饰器函数
        
    Notes:
        - 专门为异步函数设计
        - 保留了异步函数的行为和特性
        - 提供缓存统计信息和清除方法
        
    Example:
        ```python
        @async_memo(maxsize=100)
        async def fetch_user_data(user_id: int):
            # 从数据库或API获取数据
            return data
            
        # 访问缓存统计
        print(fetch_user_data.cache_info())
        ```
    """
    cache = {}
    cache_info = {"hits": 0, "misses": 0, "maxsize": maxsize, "currsize": 0}
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if maxsize == 0:  # 不缓存
                return await func(*args, **kwargs)
                
            key = _make_key(args, kwargs, typed)
            
            if key in cache:
                cache_info["hits"] += 1
                return cache[key]
                
            cache_info["misses"] += 1
            result = await func(*args, **kwargs)
            
            # 如果达到最大容量，清除最早的缓存
            if maxsize is not None and len(cache) >= maxsize:
                cache.pop(next(iter(cache.keys())))
                
            cache[key] = result
            cache_info["currsize"] = len(cache)
            return result
            
        def cache_clear():
            """清除缓存"""
            cache.clear()
            cache_info["currsize"] = 0
            
        def cache_info_func():
            """获取缓存状态信息"""
            return cache_info
            
        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info_func
        return wrapper
        
    return decorator

def timed_memo(
    maxsize: int = 128, 
    ttl: int = 600,
    typed: bool = False
):
    """
    带过期时间的内存缓存装饰器
    
    缓存函数结果，但结果会在指定时间后过期，避免使用过时数据。
    
    Args:
        maxsize: 缓存的最大条目数
        ttl: 缓存生存时间（秒）
        typed: 是否区分参数类型
        
    Returns:
        装饰器函数
        
    Notes:
        - 适用于数据会随时间变化但短期内可复用的场景
        - 懒惰过期：只在访问时检查是否过期
        - 提供缓存统计和控制方法
        
    Example:
        ```python
        @timed_memo(ttl=300)  # 缓存5分钟
        def get_weather(city):
            # 获取城市天气数据
            return weather_data
        ```
    """
    cache = {}
    cache_info = {"hits": 0, "misses": 0, "expired": 0, "maxsize": maxsize, "currsize": 0}
    
    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if maxsize == 0:  # 不缓存
                return func(*args, **kwargs)
                
            key = _make_key(args, kwargs, typed)
            current_time = time.time()
            
            if key in cache:
                value, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    cache_info["hits"] += 1
                    return value
                else:
                    # 缓存已过期
                    cache_info["expired"] += 1
                    del cache[key]
            
            cache_info["misses"] += 1
            result = func(*args, **kwargs)
            
            # 如果达到最大容量，清除最早的缓存
            if maxsize is not None and len(cache) >= maxsize:
                cache.pop(next(iter(cache.keys())))
                
            cache[key] = (result, current_time)
            cache_info["currsize"] = len(cache)
            return result
            
        # 处理异步函数
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if maxsize == 0:  # 不缓存
                    return await func(*args, **kwargs)
                    
                key = _make_key(args, kwargs, typed)
                current_time = time.time()
                
                if key in cache:
                    value, timestamp = cache[key]
                    if current_time - timestamp < ttl:
                        cache_info["hits"] += 1
                        return value
                    else:
                        # 缓存已过期
                        cache_info["expired"] += 1
                        del cache[key]
                
                cache_info["misses"] += 1
                result = await func(*args, **kwargs)
                
                # 如果达到最大容量，清除最早的缓存
                if maxsize is not None and len(cache) >= maxsize:
                    cache.pop(next(iter(cache.keys())))
                    
                cache[key] = (result, current_time)
                cache_info["currsize"] = len(cache)
                return result
                
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper
            
        def cache_clear():
            """清除缓存"""
            cache.clear()
            cache_info["currsize"] = 0
            cache_info["hits"] = 0
            cache_info["misses"] = 0
            cache_info["expired"] = 0
            
        def cache_info_func():
            """获取缓存状态信息"""
            return dict(cache_info)
            
        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info_func
        return wrapper
        
    return decorator

def typed_memo(maxsize: int = 128):
    """
    类型敏感的内存缓存装饰器
    
    对不同类型的参数使用不同的缓存，即使值相同也视为不同的输入。
    
    Args:
        maxsize: 缓存的最大条目数
        
    Returns:
        装饰器函数
        
    Notes:
        - 此装饰器是memo(typed=True)的快捷方式
        - 区分不同类型的参数，如1和1.0
        
    Example:
        ```python
        @typed_memo()
        def process_data(value):
            # 1和1.0将被视为不同的输入
            return complex_calculation(value)
        ```
    """
    return memo(maxsize=maxsize, typed=True) 