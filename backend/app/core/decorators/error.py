"""
错误处理装饰器

提供异常处理和重试机制的装饰器：
- handle_exceptions: 统一捕获并处理指定类型的异常
- retry: 在遇到特定异常时自动重试函数执行
"""

from fastapi import HTTPException, Request, Response
# from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from functools import wraps
from typing import Type, Union, Dict, Any, Callable, TypeVar, Optional, Tuple
# from typing import Type, Union, List, Dict, Any, Callable, TypeVar, Optional, Tuple
import time
import inspect
import traceback
from ...core.exceptions import (
    BusinessError, 
    APIError, 
    NotFoundError, 
    BusinessException, 
    AuthenticationError, 
    PermissionDeniedError, 
    ValidationError,
    RateLimitError,
    ResourceConflictError,
    RequestDataError
)
from ...core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

def handle_exceptions(
    exception_type: Union[Type[Exception], Tuple[Type[Exception], ...]],
    status_code: int = 500,
    message: str = "处理请求时发生错误",
    include_details: bool = False,
    log_level: str = "error",
    response_model: Optional[Type] = None
):
    """
    异常处理装饰器
    
    捕获指定类型的异常，将其转换为统一的HTTP响应。
    
    Args:
        exception_type: 要捕获的异常类型
        status_code: 发生异常时返回的HTTP状态码，默认500
        message: 发生异常时返回的错误消息
        include_details: 是否在响应中包含异常详情，默认False
        log_level: 记录异常的日志级别，默认"error"
        response_model: 自定义响应模型
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except exception_type as e:
                # 从异常中提取有用信息
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_traceback = traceback.format_exc()
                
                # 构建错误详情
                error_details = f"{exc_type}: {exc_msg}"
                
                # 获取请求上下文（如果可用）
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request and 'request' in kwargs:
                    request = kwargs['request']
                
                # 确定日志级别
                log_func = getattr(logger, log_level, logger.error)
                
                # 日志记录
                if request:
                    client_ip = request.client.host if request.client else "unknown"
                    method = request.method
                    url = str(request.url)
                    
                    log_func(
                        f"请求处理异常: {method} {url} - {error_details}",
                        extra={
                            "client_ip": client_ip,
                            "method": method,
                            "url": url,
                            "exception_type": exc_type,
                            "exception_msg": exc_msg,
                            "traceback": exc_traceback
                        }
                    )
                else:
                    log_func(
                        f"函数执行异常: {func.__name__} - {error_details}",
                        extra={
                            "function": func.__name__,
                            "exception_type": exc_type,
                            "exception_msg": exc_msg,
                            "traceback": exc_traceback
                        }
                    )
                
                # 构建错误响应
                response_data = {
                    "detail": message
                }
                
                # 包含异常详情
                if include_details:
                    if isinstance(e, BusinessError):
                        # 业务异常包含特定的错误代码和消息
                        response_data["code"] = e.code
                        response_data["message"] = e.message
                        response_data["details"] = e.details
                    else:
                        # 普通异常只包含类型和消息
                        response_data["error_type"] = exc_type
                        response_data["error_message"] = exc_msg
                
                # 如果是HTTPException，使用其状态码和标头
                if isinstance(e, HTTPException):
                    return JSONResponse(
                        status_code=e.status_code,
                        content=response_data,
                        headers=getattr(e, "headers", None)
                    )
                
                # 如果是APIError，使用其状态码和错误信息
                if isinstance(e, APIError):
                    return JSONResponse(
                        status_code=e.status_code,
                        content={
                            "error": {
                                "code": e.code,
                                "message": e.detail,
                                "status_code": e.status_code,
                                "details": e.details,
                                "request_id": e.request_id
                            }
                        }
                    )
                
                # 使用自定义响应模型（如果提供）
                if response_model:
                    try:
                        return response_model(**response_data)
                    except Exception as model_error:
                        logger.error(f"创建响应模型失败: {str(model_error)}")
                
                # 默认返回JSONResponse
                return JSONResponse(
                    status_code=status_code,
                    content=response_data
                )
        
        return wrapper
    
    return decorator

def retry(
    max_retries: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    重试装饰器
    
    在发生特定异常时自动重试函数执行。
    
    Args:
        max_retries: 最大重试次数，默认3次
        delay: 初始延迟时间（秒），默认0.1秒
        backoff: 延迟增长因子，默认2.0
        exceptions: 触发重试的异常类型，默认所有异常
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for the initial attempt
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # 已达到最大重试次数，重新抛出异常
                        logger.warning(
                            f"函数 {func.__name__} 达到最大重试次数 {max_retries}，"
                            f"最后一次异常: {type(e).__name__}: {str(e)}"
                        )
                        raise
                    
                    # 记录重试信息
                    logger.info(
                        f"函数 {func.__name__} 执行失败 (尝试 {attempt+1}/{max_retries+1})，"
                        f"异常: {type(e).__name__}: {str(e)}，"
                        f"将在 {current_delay:.2f} 秒后重试"
                    )
                    
                    # 等待后重试
                    time.sleep(current_delay)
                    current_delay *= backoff  # 指数退避
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for the initial attempt
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # 已达到最大重试次数，重新抛出异常
                        logger.warning(
                            f"函数 {func.__name__} 达到最大重试次数 {max_retries}，"
                            f"最后一次异常: {type(e).__name__}: {str(e)}"
                        )
                        raise
                    
                    # 记录重试信息
                    logger.info(
                        f"函数 {func.__name__} 执行失败 (尝试 {attempt+1}/{max_retries+1})，"
                        f"异常: {type(e).__name__}: {str(e)}，"
                        f"将在 {current_delay:.2f} 秒后重试"
                    )
                    
                    # 等待后重试
                    time.sleep(current_delay)
                    current_delay *= backoff  # 指数退避
        
        # 根据函数是否为异步选择适当的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator 

def handle_database_exception(e: Exception) -> None:
    """处理数据库相关异常，转换为适当的HTTP异常
    
    识别常见的数据库异常类型并转换为对用户友好的错误信息。
    
    Args:
        e: 捕获的异常对象
        
    Raises:
        HTTPException: 转换后的HTTP异常
    """
    error_message = str(e)
    error_code = "DATABASE_ERROR"
    status_code = 500
    
    # ... existing code ...
    
def handle_business_exception(e: BusinessException) -> None:
    """处理业务异常，根据异常类型转换为合适的HTTP异常
    
    根据异常类型返回不同的状态码和错误信息。
    - NotFoundError: 404 资源未找到
    - AuthenticationError: 401 身份验证失败
    - PermissionDeniedError: 403 权限不足
    - ValidationError: 422 数据验证失败
    - RateLimitError: 429 请求过于频繁
    - ResourceConflictError: 409 资源冲突
    - RequestDataError: 400 请求数据错误
    - 其他BusinessException: 使用异常自带的status_code或默认500
    
    Args:
        e: 业务异常对象
        
    Raises:
        HTTPException: 转换后的HTTP异常
    """
    # 根据异常类型设置默认状态码
    status_code = e.status_code if hasattr(e, 'status_code') else 500
    
    # 根据异常类型调整状态码
    if isinstance(e, NotFoundError):
        status_code = 404
    elif isinstance(e, AuthenticationError):
        status_code = 401
    elif isinstance(e, PermissionDeniedError) or isinstance(e, PermissionError):
        status_code = 403
    elif isinstance(e, ValidationError):
        status_code = 422
    elif isinstance(e, RateLimitError):
        status_code = 429
    elif isinstance(e, ResourceConflictError) or "conflict" in e.__class__.__name__.lower():
        status_code = 409
    elif isinstance(e, RequestDataError):
        status_code = 400
        
    # 构造错误详情
    detail = {
        "message": e.message if hasattr(e, 'message') else str(e),
        "error_code": e.code if hasattr(e, 'code') else "BUSINESS_ERROR"
    }
    
    # 如果有详细信息，添加到detail中
    if hasattr(e, 'details') and e.details:
        detail["details"] = e.details
        
    # 抛出适当的HTTP异常
    raise HTTPException(
        status_code=status_code,
        detail=detail
    )

def with_error_handling(default_error_message: str = "操作失败", handle_db_errors: bool = True):
    """异常处理装饰器
    
    为API端点提供统一的异常处理，捕获各种异常并转换为适当的HTTP响应。
    可以处理以下类型的异常：
    - BusinessException及其子类（NotFoundError, ValidationError等）
    - 数据库相关异常
    - 其他未预期的异常
    
    Args:
        default_error_message: 未分类异常的默认错误消息
        handle_db_errors: 是否尝试处理数据库异常
        
    Returns:
        装饰器函数
        
    Example:
        @router.get("/items/{item_id}")
        @public_endpoint()
        @with_error_handling(default_error_message="获取商品失败")
        async def get_item(item_id: int):
            return await service.get_item(item_id)
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            
            except BusinessException as e:
                # 处理业务异常
                handle_business_exception(e)
                
            except HTTPException:
                # 直接重新抛出HTTP异常
                raise
                
            except Exception as e:
                logger.error(f"执行 {func.__name__} 时发生未预期异常: {str(e)}", exc_info=True)
                
                # 尝试处理数据库异常
                if handle_db_errors:
                    try:
                        is_db_error = ("db" in str(e).lower() or 
                                      (hasattr(e, "__module__") and "sqlalchemy" in e.__module__.lower()))
                        if is_db_error:
                            handle_database_exception(e)
                    except:
                        pass
                
                # 其他未处理的异常
                raise HTTPException(
                    status_code=500,
                    detail={"message": default_error_message, "error_code": "INTERNAL_ERROR"}
                )
        
        return wrapper
    
    return decorator 