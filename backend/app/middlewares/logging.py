import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("request")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 如果响应状态码是错误状态码，记录错误日志
            if response.status_code >= 400:
                self.logger.error(
                    "Request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "url": str(request.url),
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                        "status_code": response.status_code,
                        "process_time": f"{process_time:.3f}s",
                    }
                )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            return response
            
        except Exception as e:
            # 记录请求异常
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise 