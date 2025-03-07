from fastapi import Request, Depends
from typing import Optional, Callable, Any, Dict, TypeVar
from datetime import timedelta
import hashlib
from ..core.cache import cache_manager
from ..core.logging import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
T = TypeVar('T')

async def get_cached_response(
    request: Request,
    expire: int = 300,
    cache_key_func: Optional[Callable[[Request], str]] = None,
    include_user_id: bool = False
) -> Optional[Dict[str, Any]]:
    """获取缓存的响应
    
    检查并返回请求的缓存响应。
    
    Args:
        request: FastAPI请求对象
        expire: 缓存过期时间(秒)，默认300秒
        cache_key_func: 自定义缓存键生成函数
        include_user_id: 是否在缓存键中包含用户ID
        
    Returns:
        Optional[Dict[str, Any]]: 缓存的响应数据，如果缓存未命中则返回None
    """
    # 只缓存GET请求
    if request.method != "GET":
        return None
    
    # 生成缓存键
    cache_key = await _generate_cache_key(request, cache_key_func, include_user_id)
    
    # 从缓存获取数据
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        logger.debug(f"缓存命中: {cache_key}")
    
    return cached_data

async def set_cached_response(
    request: Request,
    data: Any,
    expire: int = 300,
    cache_key_func: Optional[Callable[[Request], str]] = None,
    include_user_id: bool = False
) -> None:
    """设置响应缓存
    
    将响应数据存入缓存。
    
    Args:
        request: FastAPI请求对象
        data: 要缓存的数据
        expire: 缓存过期时间(秒)，默认300秒
        cache_key_func: 自定义缓存键生成函数
        include_user_id: 是否在缓存键中包含用户ID
    """
    # 只缓存GET请求
    if request.method != "GET":
        return
    
    # 生成缓存键
    cache_key = await _generate_cache_key(request, cache_key_func, include_user_id)
    
    # 设置缓存
    await cache_manager.set(cache_key, data, expire)
    logger.debug(f"缓存已设置: {cache_key}, 过期时间: {expire}秒")

async def _generate_cache_key(
    request: Request,
    cache_key_func: Optional[Callable[[Request], str]] = None,
    include_user_id: bool = False
) -> str:
    """生成缓存键
    
    Args:
        request: FastAPI请求对象
        cache_key_func: 自定义缓存键生成函数
        include_user_id: 是否在缓存键中包含用户ID
        
    Returns:
        str: 缓存键
    """
    if cache_key_func:
        return cache_key_func(request)
    
    # 基本缓存键：URL + 查询参数
    url = str(request.url)
    
    # 可选：添加用户ID
    user_id = None
    if include_user_id and hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("id")
    
    # 生成哈希键
    key_parts = [url]
    if user_id:
        key_parts.append(f"user:{user_id}")
    
    key_str = ":".join(key_parts)
    hashed_key = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"response_cache:{hashed_key}" 