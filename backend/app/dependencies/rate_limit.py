"""
此模块为向后兼容层，保持旧代码正常工作。
新代码应直接从 .limit 和 .cache 模块导入。

将在未来版本中移除，请更新您的导入：
- 使用 `from ..dependencies.limit import rate_limit` 代替
- 使用 `from ..dependencies.cache import get_cached_response, set_cached_response` 代替
"""

# 重新导出限流函数
from .limit import rate_limit, ip_rate_limit

# 导入类型提示
from fastapi import Request, Depends, HTTPException
from typing import Optional, Callable, Dict, Any
from ..core.logging import get_logger
from .auth import get_current_user
from ..db.models import User
from datetime import timedelta
import hashlib

# 重新导出缓存函数，兼容旧名称
from .cache import get_cached_response as cache_response
from .cache import set_cached_response as set_cache_response

# 为向后兼容保留的变量
logger = get_logger(__name__)

# 弃用警告
import warnings
warnings.warn(
    "dependencies.rate_limit 模块已弃用。请使用 dependencies.limit 和 dependencies.cache 代替。",
    DeprecationWarning,
    stacklevel=2
)

# 简化实现的内存缓存，生产环境应使用Redis等缓存系统
_mem_cache: Dict[str, Dict[str, Any]] = {}

class MemoryRateLimiter:
    """内存实现的简单限流器"""
    
    def __init__(self, limit: int, window: int):
        """初始化限流器
        
        Args:
            limit: 时间窗口内允许的最大请求数
            window: 时间窗口大小(秒)
        """
        self.limit = limit
        self.window = window
        self._counters: Dict[str, Dict[str, Any]] = {}
    
    def _clean_expired(self):
        """清理过期的计数器"""
        now = time.time()
        expired_keys = []
        
        for key, data in self._counters.items():
            if data["reset_at"] < now:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._counters[key]
    
    def is_allowed(self, key: str) -> bool:
        """检查是否允许请求
        
        Args:
            key: 请求标识符
            
        Returns:
            bool: 如果允许请求，则返回True，否则返回False
        """
        self._clean_expired()
        now = time.time()
        
        if key not in self._counters:
            self._counters[key] = {
                "count": 1,
                "reset_at": now + self.window
            }
            return True
        
        counter = self._counters[key]
        
        # 如果时间窗口已过期，重置计数器
        if counter["reset_at"] < now:
            counter["count"] = 1
            counter["reset_at"] = now + self.window
            return True
        
        # 检查是否超过限制
        if counter["count"] >= self.limit:
            return False
        
        # 增加计数
        counter["count"] += 1
        return True
    
    def time_remaining(self, key: str) -> int:
        """获取重置前的剩余时间
        
        Args:
            key: 请求标识符
            
        Returns:
            int: 重置前的剩余秒数
        """
        if key not in self._counters:
            return 0
        
        now = time.time()
        return max(0, int(self._counters[key]["reset_at"] - now))

async def rate_limit(
    request: Request,
    limit: int = 60,
    window: int = 60,
    current_user: Optional[User] = Depends(get_current_user)
):
    """API请求频率限制
    
    Args:
        request: FastAPI请求对象
        limit: 时间窗口内允许的最大请求数
        window: 时间窗口大小(秒)
        current_user: 当前用户对象
        
    Raises:
        HTTPException: 如果请求超过限制，则抛出429异常
    """
    # 获取客户端IP或用户ID作为限流标识
    client_id = request.client.host
    if current_user:
        client_id = f"user:{current_user.id}"
    
    # 结合请求路径，对不同的API端点分别限流
    path = request.url.path
    rate_limit_key = f"rate_limit:{path}:{client_id}"
    
    # 创建限流器
    limiter = MemoryRateLimiter(limit=limit, window=window)
    
    # 检查是否允许请求
    if not limiter.is_allowed(rate_limit_key):
        remaining = limiter.time_remaining(rate_limit_key)
        logger.warning(f"请求限流: {client_id}, 路径: {path}, 剩余时间: {remaining}秒")
        raise HTTPException(
            status_code=429,
            detail=f"请求太频繁，请在{remaining}秒后重试"
        )
    
    # 允许请求通过
    return True

async def cache_response(
    request: Request,
    cache_key_func: Optional[Callable[[Request], str]] = None,
    expire: int = 300
):
    """响应缓存中间件
    
    Args:
        request: FastAPI请求对象
        cache_key_func: 自定义缓存键生成函数
        expire: 缓存过期时间(秒)
        
    Returns:
        Optional[Dict]: 如果缓存命中，则返回缓存数据，否则返回None
    """
    # 只缓存GET请求
    if request.method != "GET":
        return None
    
    # 生成缓存键
    if cache_key_func:
        cache_key = cache_key_func(request)
    else:
        # 默认使用完整URL作为缓存键
        path = str(request.url)
        path_hash = hashlib.md5(path.encode()).hexdigest()
        cache_key = f"response_cache:{path_hash}"
    
    # 尝试从缓存获取数据
    global _mem_cache
    now = time.time()
    
    if cache_key in _mem_cache:
        cache_data = _mem_cache[cache_key]
        # 检查是否过期
        if cache_data["expires_at"] > now:
            logger.debug(f"缓存命中: {cache_key}")
            return cache_data["data"]
        else:
            # 清理过期缓存
            del _mem_cache[cache_key]
    
    return None

def set_cache_response(cache_key: str, data: Any, expire: int = 300):
    """设置响应缓存
    
    Args:
        cache_key: 缓存键
        data: 要缓存的数据
        expire: 缓存过期时间(秒)
    """
    global _mem_cache
    now = time.time()
    
    _mem_cache[cache_key] = {
        "data": data,
        "expires_at": now + expire
    }
    
    # 简单的缓存清理
    if len(_mem_cache) > 1000:  # 避免内存泄漏
        _clean_expired_cache()

def _clean_expired_cache():
    """清理过期的缓存项"""
    global _mem_cache
    now = time.time()
    expired_keys = []
    
    for key, cache_data in _mem_cache.items():
        if cache_data["expires_at"] < now:
            expired_keys.append(key)
    
    for key in expired_keys:
        del _mem_cache[key] 