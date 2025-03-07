from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import timedelta
from typing import Callable
from ..core.cache import RateLimiter
from ..core.config import settings
from ..core.exceptions import APIError
from ..core.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 开发环境下完全禁用速率限制
        # 或者豁免常用API端点
        if (
            # 豁免常用API端点
            request.url.path.endswith("/captcha/generate") or 
            "/posts" in request.url.path or
            "/users" in request.url.path or
            "/auth" in request.url.path or
            "/sections" in request.url.path or
            "/comments" in request.url.path or
            # 豁免API文档
            request.url.path.endswith("/docs") or
            request.url.path.endswith("/openapi.json") or
            # 豁免OPTIONS请求（CORS预检请求）
            request.method == "OPTIONS"
        ):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        
        # 记录请求信息，便于调试
        logger.info(
            f"速率限制检查: {client_ip} - {request.method} {request.url.path}"
        )
        
        if not await RateLimiter.is_allowed(
            "api",
            client_ip,
            settings.RATE_LIMIT_REQUESTS,
            timedelta(seconds=settings.RATE_LIMIT_WINDOW)
        ):
            logger.warning(
                f"速率限制触发: {client_ip} - {request.method} {request.url.path}"
            )
            raise APIError(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        return await call_next(request) 