"""
错误处理装饰器模块

提供用于异常处理和错误恢复的装饰器：
- handle_exceptions: 统一异常处理
- retry: 自动重试

所有装饰器都支持异步函数，并提供完整的类型提示。
"""

from functools import wraps
from typing import Any, Callable, Type, Optional, List, Union, Dict
import time
import asyncio
import inspect

from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from .logging import get_logger
from .context_managers import error_boundary
from .decorator_config import get_config

logger = get_logger(__name__)

def handle_exceptions(
    *exceptions: Type[Exception],
    status_code: Optional[int] = None,
    message: Optional[str] = None,
    include_details: Optional[bool] = None,
    log_error: Optional[bool] = None
):
    """
    异常处理装饰器
    
    捕获指定的异常类型，并转换为标准的HTTP错误响应。
    
    Args:
        *exceptions: 要捕获的异常类型
        status_code: HTTP状态码，不指定则使用配置默认值
        message: 错误消息，不指定则使用配置默认值
        include_details: 是否在响应中包含详细错误信息，不指定则使用配置默认值
        log_error: 是否记录异常日志，不指定则使用配置默认值
        
    Returns:
        Callable: 装饰器函数
        
    Example:
        @handle_exceptions(ValueError, TypeError, status_code=400)
        async def my_handler():
            ...
    """
    # 获取配置
    config = get_config().exception_handler
    
    # 使用传入参数或配置默认值
    _status_code = status_code if status_code is not None else config.default_status_code
    _message = message if message is not None else config.default_message
    _include_details = include_details if include_details is not None else config.include_details
    _log_error = log_error if log_error is not None else config.log_traceback
    
    # 如果没有提供异常类型，默认捕获所有异常
    _exceptions = exceptions if exceptions else (Exception,)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 定义异常处理函数
            def on_error(e: Exception) -> None:
                # 构建错误上下文
                error_context = {
                    "function": func.__name__,
                    "error_type": e.__class__.__name__,
                    "error": str(e),
                }
                
                # 记录错误日志
                if _log_error:
                    logger.error(
                        f"执行{func.__name__}时发生错误: {str(e)}",
                        exc_info=True,
                        extra=error_context
                    )
                
                # 构建错误响应
                error_detail = {
                    "message": _message,
                }
                
                # 如果配置要包含详细信息，添加到响应中
                if _include_details:
                    error_detail["detail"] = str(e)
                    error_detail["error_type"] = e.__class__.__name__
                
                # 抛出HTTP异常
                raise HTTPException(
                    status_code=_status_code,
                    detail=error_detail
                )
            
            # 使用错误处理上下文执行函数
            with error_boundary(
                *_exceptions,
                default_value=None,
                logger=logger
            ):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def retry(
    max_retries: Optional[int] = None,
    delay: Optional[float] = None,
    backoff: Optional[bool] = None,
    backoff_factor: Optional[float] = None,
    max_delay: Optional[float] = None,
    retry_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    重试装饰器
    
    在发生特定异常时自动重试函数执行。
    
    Args:
        max_retries: 最大重试次数，不指定则使用配置默认值
        delay: 重试间隔（秒），不指定则使用配置默认值
        backoff: 是否使用指数退避策略，不指定则使用配置默认值
        backoff_factor: 退避因子，不指定则使用配置默认值
        max_delay: 最大延迟时间（秒），不指定则使用配置默认值
        retry_exceptions: 要重试的异常类型列表，不指定则使用配置默认值
        
    Returns:
        Callable: 装饰器函数
        
    Example:
        @retry(max_retries=3, delay=1, retry_exceptions=[ConnectionError])
        async def fetch_data():
            ...
    """
    # 获取配置
    config = get_config().retry
    
    # 使用传入参数或配置默认值
    _max_retries = max_retries if max_retries is not None else config.max_retries
    _delay = delay if delay is not None else config.delay
    _backoff = backoff if backoff is not None else config.backoff
    _backoff_factor = backoff_factor if backoff_factor is not None else config.backoff_factor
    _max_delay = max_delay if max_delay is not None else config.max_delay
    
    # 处理retry_exceptions
    _retry_exceptions = retry_exceptions
    if _retry_exceptions is None and config.retry_exceptions:
        # 将字符串类型名称转换为实际异常类
        _retry_exceptions = []
        for exception_name in config.retry_exceptions:
            try:
                exception_class = eval(exception_name)
                if issubclass(exception_class, Exception):
                    _retry_exceptions.append(exception_class)
            except (NameError, TypeError):
                logger.warning(f"未知异常类型: {exception_name}")
        
        # 如果没有有效的异常类型，捕获所有异常
        if not _retry_exceptions:
            _retry_exceptions = [Exception]
    elif _retry_exceptions is None:
        _retry_exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            current_delay = _delay
            
            while True:
                try:
                    # 尝试执行函数
                    return await func(*args, **kwargs)
                
                except tuple(_retry_exceptions) as e:
                    # 处理重试逻辑
                    retries += 1
                    should_retry, current_delay = _handle_retry(
                        func.__name__, retries, _max_retries, current_delay, 
                        _backoff, _backoff_factor, _max_delay, e, config
                    )
                    if not should_retry:
                        raise
                    
                    # 等待一段时间后重试
                    await asyncio.sleep(current_delay)
                        
                except Exception as e:
                    # 对于未配置重试的异常类型，直接抛出
                    logger.error(
                        f"执行{func.__name__}时发生非重试异常: {str(e)}",
                        exc_info=True
                    )
                    raise
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            current_delay = _delay
            
            while True:
                try:
                    # 尝试执行函数
                    return func(*args, **kwargs)
                
                except tuple(_retry_exceptions) as e:
                    # 处理重试逻辑
                    retries += 1
                    should_retry, current_delay = _handle_retry(
                        func.__name__, retries, _max_retries, current_delay, 
                        _backoff, _backoff_factor, _max_delay, e, config
                    )
                    if not should_retry:
                        raise
                    
                    # 等待一段时间后重试
                    time.sleep(current_delay)
                        
                except Exception as e:
                    # 对于未配置重试的异常类型，直接抛出
                    logger.error(
                        f"执行{func.__name__}时发生非重试异常: {str(e)}",
                        exc_info=True
                    )
                    raise
        
        # 根据函数类型返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return wrapper
        return sync_wrapper
    
    return decorator

def _handle_retry(
    func_name: str, 
    retries: int, 
    max_retries: int, 
    current_delay: float,
    backoff: bool,
    backoff_factor: float,
    max_delay: float,
    exception: Exception,
    config: Any
) -> tuple[bool, float]:
    """
    处理重试逻辑
    
    Args:
        func_name: 函数名称
        retries: 当前重试次数
        max_retries: 最大重试次数
        current_delay: 当前延迟时间
        backoff: 是否使用指数退避
        backoff_factor: 退避因子
        max_delay: 最大延迟时间
        exception: 捕获的异常
        config: 重试配置
        
    Returns:
        tuple: (是否应该重试, 下一次延迟时间)
    """
    # 如果达到最大重试次数，不再重试
    if retries > max_retries:
        logger.warning(
            f"执行{func_name}达到最大重试次数({max_retries})，放弃重试",
            extra={
                "function": func_name,
                "max_retries": max_retries,
                "error": str(exception)
            }
        )
        return False, current_delay
    
    # 记录重试日志
    if config.log_before_retry:
        logger.info(
            f"执行{func_name}失败，{current_delay:.1f}秒后进行第{retries}次重试",
            extra={
                "function": func_name,
                "retry_count": retries,
                "delay": current_delay,
                "error": str(exception)
            }
        )
    
    # 如果使用指数退避，计算下一次延迟时间
    next_delay = current_delay
    if backoff:
        next_delay = min(current_delay * backoff_factor, max_delay)
        
    return True, next_delay 