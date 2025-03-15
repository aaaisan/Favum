"""
错误处理中间件

为FastAPI应用提供统一的错误处理，将各种异常转换为格式一致的响应。
"""

import time
import traceback
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.exceptions import BusinessException

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    全局错误处理中间件
    
    捕获请求处理过程中的异常，并将其转换为统一格式的JSON响应。
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并捕获异常
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        request_id = f"{int(time.time() * 1000)}-{id(request)}"
        start_time = time.time()
        
        try:
            # 设置请求ID上下文
            request.state.request_id = request_id
            
            # 处理请求
            response = await call_next(request)
            
            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            
            # 计算处理时间
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            return response
            
        except BusinessException as e:
            # 处理业务异常
            return self._handle_business_error(e, request_id)
            
        except HTTPException as e:
            # 处理HTTP异常
            return self._handle_http_exception(e, request_id)
            
        except RequestValidationError as e:
            # 处理请求验证异常
            return self._handle_validation_error(e, request_id)
            
        except Exception as e:
            # 处理其他未预期的异常
            return self._handle_unexpected_error(e, request_id)
    
    def _handle_business_error(self, exc: BusinessException, request_id: str) -> JSONResponse:
        """
        处理业务异常
        
        Args:
            exc: 业务异常
            request_id: 请求ID
            
        Returns:
            JSON响应
        """
        error_data = exc.to_dict()
        error_data["request_id"] = request_id
        
        logger.warning(
            f"业务异常: {exc.code} - {exc.message}",
            extra={"request_id": request_id, "status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_data}
        )
    
    def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """
        处理HTTP异常
        
        Args:
            exc: HTTP异常
            request_id: 请求ID
            
        Returns:
            JSON响应
        """
        error_data = {
            "code": f"http_{exc.status_code}",
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "request_id": request_id
        }
        
        logger.warning(
            f"HTTP异常: {exc.status_code} - {exc.detail}",
            extra={"request_id": request_id, "status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_data}
        )
    
    def _handle_validation_error(self, exc: RequestValidationError, request_id: str) -> JSONResponse:
        """
        处理请求验证异常
        
        Args:
            exc: 请求验证异常
            request_id: 请求ID
            
        Returns:
            JSON响应
        """
        # 格式化验证错误
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
        
        error_data = {
            "code": "validation_error",
            "message": "请求参数验证失败",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": error_details,
            "request_id": request_id
        }
        
        logger.warning(
            f"请求验证异常: {len(error_details)}个错误",
            extra={"request_id": request_id, "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": error_data}
        )
    
    def _handle_unexpected_error(self, exc: Exception, request_id: str) -> JSONResponse:
        """
        处理未预期的异常
        
        Args:
            exc: 未预期的异常
            request_id: 请求ID
            
        Returns:
            JSON响应
        """
        error_data = {
            "code": "internal_server_error",
            "message": "服务器内部错误",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": request_id
        }
        
        # 记录详细的错误信息
        trace = traceback.format_exc()
        logger.error(
            f"未预期的异常: {str(exc)}\n{trace}",
            extra={"request_id": request_id, "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}
        )
        
        # 在开发环境可以添加更多详细信息
        if logger.level <= logging.DEBUG:
            error_data["details"] = {
                "exception": str(exc),
                "traceback": trace.split("\n")
            }
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": error_data}
        )

def add_error_handler(app: FastAPI):
    """
    添加错误处理中间件到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 注册特定异常处理器
    @app.exception_handler(BusinessException)
    async def business_error_handler(request: Request, exc: BusinessException):
        request_id = getattr(request.state, "request_id", "unknown")
        middleware = ErrorHandlerMiddleware(None)
        return middleware._handle_business_error(exc, request_id)
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        middleware = ErrorHandlerMiddleware(None)
        return middleware._handle_validation_error(exc, request_id)
        
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "unknown")
        middleware = ErrorHandlerMiddleware(None)
        return middleware._handle_http_exception(exc, request_id)
    
    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        middleware = ErrorHandlerMiddleware(None)
        return middleware._handle_unexpected_error(exc, request_id) 