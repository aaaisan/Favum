from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import timedelta
from typing import Callable
from ...core.cache import RateLimiter
from ...core.config import settings
from ...core.exceptions import APIError

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host if request.client else "unknown"
        
        if not RateLimiter.is_allowed(
            "api",
            client_ip,
            settings.RATE_LIMIT_REQUESTS,
            timedelta(seconds=settings.RATE_LIMIT_WINDOW)
        ):
            raise APIError(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        return await call_next(request) 