from fastapi import Request, Depends, HTTPException
from typing import Optional
from datetime import timedelta
from ..core.cache import RateLimiter
from ..core.logging import get_logger
from ..db.models import User
from .auth import get_current_user

logger = get_logger(__name__)

async def rate_limit(
    request: Request,
    limit: int = 60,
    window: int = 60,
    current_user: Optional[User] = Depends(get_current_user)
):
    """API请求频率限制
    
    基于Redis的速率限制依赖函数，可以应用于任何FastAPI路由。
    
    Args:
        request: FastAPI请求对象
        limit: 时间窗口内允许的最大请求数，默认60
        window: 时间窗口大小(秒)，默认60秒
        current_user: 当前用户对象（由get_current_user依赖注入）
        
    Raises:
        HTTPException: 如果请求超过限制，则抛出429异常
        
    Returns:
        bool: 如果请求未超过限制，则返回True
    """
    # 获取客户端IP或用户ID作为限流标识
    client_id = request.client.host
    if current_user:
        client_id = f"user:{current_user.id}"
    
    # 结合请求路径，对不同的API端点分别限流
    path = request.url.path
    
    # 记录请求信息，便于调试
    logger.debug(
        f"速率限制检查: {client_id} - {request.method} {request.url.path}, "
        f"限制: {limit}/{window}秒"
    )
    
    # 使用核心RateLimiter来执行限流检查
    is_allowed = await RateLimiter.is_allowed(
        f"api:{path}",  # 使用路径作为前缀区分不同API
        client_id,
        limit,
        timedelta(seconds=window)
    )
    
    if not is_allowed:
        logger.warning(
            f"速率限制触发: {client_id} - {request.method} {path}"
        )
        raise HTTPException(
            status_code=429,
            detail=f"请求太频繁，请稍后再试"
        )
    
    return True

# 可以根据需要添加更多函数，例如基于IP的限流、特定用户组的限流等
async def ip_rate_limit(
    request: Request,
    limit: int = 30,
    window: int = 60
):
    """基于IP的速率限制
    
    更简单的速率限制依赖函数，仅基于客户端IP进行限流。
    
    Args:
        request: FastAPI请求对象
        limit: 时间窗口内允许的最大请求数，默认30
        window: 时间窗口大小(秒)，默认60秒
        
    Raises:
        HTTPException: 如果请求超过限制，则抛出429异常
    """
    client_ip = request.client.host
    
    is_allowed = await RateLimiter.is_allowed(
        "ip_limit",
        client_ip,
        limit,
        timedelta(seconds=window)
    )
    
    if not is_allowed:
        logger.warning(f"IP速率限制触发: {client_ip} - {request.method} {request.url.path}")
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试"
        )
    
    return True 