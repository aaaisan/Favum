"""
日志相关装饰器

提供函数执行日志和异常日志功能的装饰器：
- log_execution_time: 记录函数执行时间
- log_exception: 记录函数执行过程中的异常
"""

from functools import wraps
from typing import TypeVar, Callable, Any, Optional, Union, Type
# from typing import TypeVar, Callable, Dict, Any, Optional, Union, Type
import time
import inspect
import traceback
import logging
from datetime import datetime
import uuid
from ...core.logging import get_logger

T = TypeVar('T')

def log_execution_time(
    level: int = logging.DEBUG,
    message: str = "函数 {function_name} 执行时间: {execution_time:.6f} 秒"
):
    """
    记录函数执行时间的装饰器
    
    Args:
        level: 日志级别，默认为DEBUG
        message: 日志消息模板，支持{function_name}和{execution_time}占位符
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 获取专用的日志器
        logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            result = None
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                log_msg = message.format(
                    function_name=func.__qualname__,
                    execution_time=execution_time
                )
                logger.log(level, log_msg, extra={
                    "execution_time": execution_time,
                    "function": func.__qualname__,
                    "module": func.__module__,
                    "result_type": type(result).__name__ if result is not None else None
                })
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            result = None
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                log_msg = message.format(
                    function_name=func.__qualname__,
                    execution_time=execution_time
                )
                logger.log(level, log_msg, extra={
                    "execution_time": execution_time,
                    "function": func.__qualname__,
                    "module": func.__module__,
                    "result_type": type(result).__name__ if result is not None else None
                })
        
        # 根据函数类型选择合适的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

def log_exception(
    level: int = logging.ERROR,
    message: str = "函数 {function_name} 执行异常: {exception_type}: {exception_message}",
    reraise: bool = True,
    log_args: bool = False,
    log_traceback: bool = True,
    exclude_exception_types: Optional[Union[Type[Exception], tuple]] = None
):
    """
    记录函数异常的装饰器
    
    Args:
        level: 日志级别，默认为ERROR
        message: 日志消息模板
        reraise: 是否重新抛出异常，默认为True
        log_args: 是否记录函数参数，默认为False
        log_traceback: 是否记录异常堆栈，默认为True
        exclude_exception_types: 不记录的异常类型
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 获取专用的日志器
        logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 检查是否应该跳过此类异常
                if exclude_exception_types and isinstance(e, exclude_exception_types):
                    if reraise:
                        raise
                    return None
                
                # 获取异常信息
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_traceback = traceback.format_exc() if log_traceback else None
                
                # 格式化日志消息
                log_msg = message.format(
                    function_name=func.__qualname__,
                    exception_type=exc_type,
                    exception_message=exc_msg
                )
                
                # 准备额外日志信息
                extra = {
                    "function": func.__qualname__,
                    "module": func.__module__,
                    "exception_type": exc_type,
                    "exception_message": exc_msg,
                    "time": datetime.now().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
                
                # 添加参数信息（如果需要）
                if log_args:
                    # 过滤掉敏感参数（如密码）
                    safe_args = [_safe_repr(arg) for arg in args]
                    safe_kwargs = {k: _safe_repr(v) for k, v in kwargs.items()}
                    extra["args"] = safe_args
                    extra["kwargs"] = safe_kwargs
                
                # 添加堆栈信息（如果需要）
                if log_traceback:
                    extra["traceback"] = exc_traceback
                
                # 记录日志
                logger.log(level, log_msg, extra=extra)
                
                # 重新抛出异常（如果需要）
                if reraise:
                    raise
                
                return None
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否应该跳过此类异常
                if exclude_exception_types and isinstance(e, exclude_exception_types):
                    if reraise:
                        raise
                    return None
                
                # 获取异常信息
                exc_type = type(e).__name__
                exc_msg = str(e)
                exc_traceback = traceback.format_exc() if log_traceback else None
                
                # 格式化日志消息
                log_msg = message.format(
                    function_name=func.__qualname__,
                    exception_type=exc_type,
                    exception_message=exc_msg
                )
                
                # 准备额外日志信息
                extra = {
                    "function": func.__qualname__,
                    "module": func.__module__,
                    "exception_type": exc_type,
                    "exception_message": exc_msg,
                    "time": datetime.now().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
                
                # 添加参数信息（如果需要）
                if log_args:
                    # 过滤掉敏感参数（如密码）
                    safe_args = [_safe_repr(arg) for arg in args]
                    safe_kwargs = {k: _safe_repr(v) for k, v in kwargs.items()}
                    extra["args"] = safe_args
                    extra["kwargs"] = safe_kwargs
                
                # 添加堆栈信息（如果需要）
                if log_traceback:
                    extra["traceback"] = exc_traceback
                
                # 记录日志
                logger.log(level, log_msg, extra=extra)
                
                # 重新抛出异常（如果需要）
                if reraise:
                    raise
                
                return None
        
        # 根据函数类型选择合适的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

def _safe_repr(obj: Any) -> str:
    """生成对象的安全表示，过滤敏感数据"""
    if isinstance(obj, dict):
        return {k: '******' if _is_sensitive_key(k) else _safe_repr(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_repr(x) for x in obj]
    else:
        return repr(obj)

def _is_sensitive_key(key: str) -> bool:
    """检查键是否包含敏感信息"""
    sensitive_keys = {
        'password', 'passwd', 'secret', 'token', 'auth', 'key', 'apikey', 
        'api_key', 'credentials', 'private', 'pwd', 'credit_card'
    }
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in sensitive_keys) 