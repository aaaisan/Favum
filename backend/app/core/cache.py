from __future__ import annotations
from typing import Any, Optional, Union, List, Dict, TypeVar, Callable
from datetime import timedelta
import json
import redis.asyncio
from redis.exceptions import RedisError
from .config import settings
from .logging import get_logger
import msgpack
import time
from functools import wraps

logger = get_logger(__name__)

T = TypeVar('T')

def redis_error_handler(default_value: Any = None):
    """Redis错误处理装饰器
    
    自动处理Redis操作中的异常，记录日志并返回默认值。
    
    Args:
        default_value: 发生错误时返回的默认值
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except RedisError as e:
                # 获取方法所属的类名（如果有）
                cls_name = args[0].__class__.__name__ if args else ""
                # 构建详细的日志信息
                operation = func.__name__.replace('_', ' ')
                logger.error(
                    f"Redis操作失败: {operation}",
                    extra={
                        "class": cls_name,
                        "function": func.__name__,
                        "error": str(e),
                        "args": str(args[1:] if cls_name else args),  # 排除self参数
                        "kwargs": str(kwargs)
                    }
                )
                return default_value
        return wrapper
    return decorator

class RedisClient:
    """Redis客户端单例类
    
    确保整个应用使用同一个Redis连接实例，避免重复创建连接。
    使用单例模式管理Redis连接，提供全局访问点。
    
    Attributes:
        _instance: 类变量，存储Redis客户端实例
        _retry_count: 重试次数
        _retry_delay: 重试延迟（秒）
    """
    _instance = None
    _retry_count = 3
    _retry_delay = 1  # 秒
    
    @classmethod
    async def get_instance(cls) -> redis.asyncio.Redis:
        """获取Redis客户端实例
        
        如果实例不存在则创建新实例，否则返回现有实例。
        使用settings中的配置初始化Redis连接。
        
        Returns:
            redis.asyncio.Redis: Redis客户端实例
            
        Raises:
            RedisError: Redis连接失败时抛出异常
        """
        if cls._instance is None:
            for attempt in range(cls._retry_count):
                try:
                    cls._instance = await redis.asyncio.Redis.from_url(
                        settings._get_redis_url(),
                        socket_timeout=settings.REDIS_TIMEOUT,
                        decode_responses=True,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                    # 测试连接
                    await cls._instance.ping()
                    break
                except RedisError as e:
                    if attempt == cls._retry_count - 1:
                        logger.error(f"Redis连接失败: {str(e)}")
                        raise
                    time.sleep(cls._retry_delay)
        return cls._instance

class CacheManager:
    """缓存管理器类
    
    提供高级缓存操作接口，包括：
    - 序列化和反序列化
    - 设置和获取缓存
    - 删除和清理缓存
    - 批量操作
    - 健康检查
    
    使用Redis作为缓存后端，支持过期时间设置。
    """
    
    def __init__(self, namespace: str = ""):
        """初始化缓存管理器
        
        Args:
            namespace: 缓存键命名空间
        """
        self._redis = None
        self._namespace = namespace
    
    async def initialize(self):
        """异步初始化Redis连接"""
        if self._redis is None:
            self._redis = await RedisClient.get_instance()
        return self
    
    def _get_key(self, key: str) -> str:
        """生成带命名空间的缓存键
        
        Args:
            key: 原始缓存键
            
        Returns:
            str: 带命名空间的缓存键
        """
        return f"{self._namespace}:{key}" if self._namespace else key
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值
        
        使用msgpack进行序列化，比JSON更快更紧凑
        
        Args:
            value: 要序列化的值
            
        Returns:
            bytes: 序列化后的字节串
        """
        try:
            return msgpack.packb(value, use_bin_type=True)
        except (TypeError, ValueError) as e:
            logger.error(f"序列化失败: {str(e)}")
            return json.dumps(value).encode()
    
    def _deserialize(self, value: Optional[bytes]) -> Any:
        """反序列化值
        
        尝试使用msgpack反序列化，失败则使用JSON
        
        Args:
            value: 要反序列化的字节串
            
        Returns:
            Any: 反序列化后的值
        """
        if value is None:
            return None
        try:
            return msgpack.unpackb(value, raw=False)
        except Exception:
            try:
                return json.loads(value)
            except Exception as e:
                logger.error(f"反序列化失败: {str(e)}")
                return None
    
    @redis_error_handler(None)
    async def get(self, key: str) -> Any:
        """获取缓存值"""
        value = await self._redis.get(self._get_key(key))
        return self._deserialize(value)
    
    @redis_error_handler(False)
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        key = self._get_key(key)
        value = self._serialize(value)
        if expire:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            return await self._redis.setex(key, expire, value)
        return await self._redis.set(key, value)
    
    @redis_error_handler(0)
    async def delete(self, *keys: str) -> int:
        """删除缓存"""
        keys_with_namespace = [self._get_key(k) for k in keys]
        return await self._redis.delete(*keys_with_namespace)
    
    @redis_error_handler(False)
    async def exists(self, *keys: str) -> bool:
        """检查缓存是否存在"""
        keys_with_namespace = [self._get_key(k) for k in keys]
        return bool(await self._redis.exists(*keys_with_namespace))
    
    @redis_error_handler(None)
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数"""
        return await self._redis.incrby(self._get_key(key), amount)
    
    @redis_error_handler(False)
    async def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """设置过期时间"""
        if isinstance(time, timedelta):
            time = int(time.total_seconds())
        return bool(await self._redis.expire(self._get_key(key), time))
    
    @redis_error_handler(0)
    async def clear_prefix(self, prefix: str) -> int:
        """清除指定前缀的所有缓存"""
        keys = await self._redis.keys(f"{prefix}*")
        if keys:
            return await self.delete(*keys)
        return 0
    
    @redis_error_handler({})
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存"""
        keys_with_namespace = [self._get_key(k) for k in keys]
        values = await self._redis.mget(keys_with_namespace)
        return {
            key: self._deserialize(value)
            for key, value in zip(keys, values)
            if value is not None
        }
    
    @redis_error_handler(False)
    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """批量设置缓存"""
        serialized = {
            self._get_key(k): self._serialize(v)
            for k, v in mapping.items()
        }
        pipe = self._redis.pipeline()
        pipe.mset(serialized)
        if expire:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            for key in serialized:
                pipe.expire(key, expire)
        await pipe.execute()
        return True
    
    @redis_error_handler(False)
    async def health_check(self) -> bool:
        """检查Redis连接是否正常"""
        return bool(await self._redis.ping())

# 创建缓存管理器实例（注意：需要在应用启动时调用initialize方法）
cache_manager = CacheManager()

class UserCache:
    """用户缓存类
    
    专门用于处理用户数据的缓存操作，提供：
    - 用户数据的缓存和获取
    - 缓存过期时间控制
    - 缓存键生成规则
    """
    PREFIX = "user"
    EXPIRE = 3600  # 1小时
    
    @staticmethod
    def get_key(user_id: int) -> str:
        """生成用户缓存键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 缓存键
        """
        return f"{UserCache.PREFIX}:{user_id}"
    
    @staticmethod
    @redis_error_handler(None)
    async def set_user(user_id: int, user_data: dict) -> None:
        """缓存用户数据
        
        Args:
            user_id: 用户ID
            user_data: 用户数据字典
        """
        await cache_manager.set(
            UserCache.get_key(user_id),
            user_data,
            UserCache.EXPIRE
        )
    
    @staticmethod
    @redis_error_handler(None)
    async def get_user(user_id: int) -> Optional[dict]:
        """获取缓存的用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[dict]: 用户数据字典，不存在则返回None
        """
        data = await cache_manager.get(UserCache.get_key(user_id))
        return data
    
    @staticmethod
    @redis_error_handler(None)
    async def delete_user(user_id: int) -> None:
        """删除用户缓存
        
        Args:
            user_id: 用户ID
        """
        await cache_manager.delete(UserCache.get_key(user_id))

class RateLimiter:
    """速率限制器类
    
    提供基于Redis的速率限制功能：
    - 请求计数
    - 时间窗口控制
    - 自定义限制规则
    """
    
    @staticmethod
    def _generate_key(prefix: str, identifier: str) -> str:
        """生成限流键
        
        Args:
            prefix: 键前缀
            identifier: 标识符（如IP地址）
            
        Returns:
            str: 限流键
        """
        return f"rate_limit:{prefix}:{identifier}"
    
    @staticmethod
    @redis_error_handler(False)
    async def is_allowed(
        prefix: str,
        identifier: str,
        max_requests: int,
        window: timedelta
    ) -> bool:
        """检查是否允许请求
        
        基于滑动窗口算法进行速率限制
        
        Args:
            prefix: 限流键前缀
            identifier: 请求标识符
            max_requests: 最大请求次数
            window: 时间窗口
            
        Returns:
            bool: 是否允许请求
        """
        key = RateLimiter._generate_key(prefix, identifier)
        # 使用pipeline减少网络往返
        pipe = cache_manager._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, int(window.total_seconds()))
        result = await pipe.execute()
        
        current = result[0]  # 获取incr的结果
        return current <= max_requests 