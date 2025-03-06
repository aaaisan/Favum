"""
中间件配置模块

提供应用级别的中间件功能，包括：
- 性能监控：记录请求处理时间
- 错误处理：统一异常处理
- 请求日志：记录错误请求信息
- 速率限制：防止请求过载
- CORS：跨域资源共享
- 可信主机：限制允许的主机
- Gzip压缩：减小响应体积

中间件按照特定顺序应用，确保正确的请求处理流程。
所有中间件都支持异步处理，适用于高并发场景。
"""

from datetime import timedelta
from typing import Callable
from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp
import time

from .config import settings
from .exceptions import APIError
from ..middlewares import RequestLoggingMiddleware, RateLimitMiddleware
from ..core.logging import get_logger

logger = get_logger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    监控和记录请求处理时间，用于：
    - 检测慢请求
    - 记录处理时间
    - 添加性能指标响应头
    
    配置：
    - 通过settings.SLOW_API_THRESHOLD设置慢请求阈值
    - 超过阈值的请求会记录警告日志
    - 所有请求都会添加X-Process-Time响应头
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并监控性能
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: FastAPI响应对象
            
        Notes:
            - 记录请求开始时间
            - 调用下一个处理器
            - 计算处理时间
            - 对于慢请求记录警告日志
            - 添加处理时间响应头
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录处理时间超过阈值的请求
        if process_time > settings.SLOW_API_THRESHOLD:
            logger.warning(
                "检测到慢请求",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": f"{process_time:.3f}s"
                }
            )
        
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        return response

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    错误处理中间件
    
    提供统一的异常处理机制：
    - 捕获所有未处理的异常
    - 转换为标准的API错误响应
    - 记录错误日志
    - 保持自定义API错误的原始信息
    
    Notes:
        - APIError异常会保持原样抛出
        - 其他异常会转换为500内部服务器错误
        - 所有未处理的异常都会记录到错误日志
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并捕获异常
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: FastAPI响应对象
            
        Raises:
            APIError: 当发生API错误时
            
        Notes:
            - 捕获所有异常
            - APIError直接重新抛出
            - 其他异常转换为500错误
            - 记录未处理的异常
        """
        try:
            return await call_next(request)
        except Exception as e:
            if isinstance(e, APIError):
                raise e
            
            logger.exception("未处理的异常")
            raise APIError(
                status_code=500,
                detail="服务器内部错误"
            )

def setup_middleware(app: FastAPI) -> None:
    """
    配置应用中间件
    
    为FastAPI应用添加所有必要的中间件，按照以下顺序：
    1. CORS处理
    2. 错误处理
    3. 请求日志
    4. 性能监控
    5. 速率限制
    6. 可信主机
    7. Gzip压缩
    
    Args:
        app: FastAPI应用实例
        
    Notes:
        - 中间件顺序很重要，影响请求处理流程
        - 每个中间件都可以通过配置文件调整参数
    """
    # 添加中间件（按照处理顺序排列）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-Captcha-ID"],
        max_age=3600,
    )
    app.add_middleware(ErrorHandlerMiddleware)  # 错误处理
    app.add_middleware(RequestLoggingMiddleware)  # 请求日志
    app.add_middleware(PerformanceMiddleware)  # 性能监控
    # app.add_middleware(RateLimitMiddleware)  # 速率限制 - 暂时禁用以解决429错误
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # 压缩响应
    
    logger.error("中间件配置完成") 