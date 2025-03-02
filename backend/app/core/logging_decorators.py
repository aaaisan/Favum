"""
日志装饰器模块

提供用于日志记录的装饰器：
- log_exception: 异常日志记录

所有装饰器都支持异步函数，并提供完整的类型提示。
"""

from functools import wraps
from typing import Any, Callable, Optional, Dict, List, Tuple
import logging
import inspect
import asyncio

from .decorator_config import get_config

def _build_log_context(
    func: Callable,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    sensitive_params: List[str],
    config
) -> Dict[str, Any]:
    """
    构建日志上下文
    
    为日志记录构建包含函数信息和安全处理后参数的上下文。
    
    Args:
        func: 被装饰的函数
        args: 位置参数
        kwargs: 关键字参数
        sensitive_params: 敏感参数列表
        config: 日志配置
        
    Returns:
        Dict[str, Any]: 日志上下文字典
    """
    # 构建基本上下文
    context = {
        "function_name": func.__name__,
        "module": func.__module__,
    }
    
    # 如果配置要求记录参数
    if config.log_args:
        # 复制kwargs并隐藏敏感参数
        safe_kwargs = kwargs.copy()
        for param in sensitive_params:
            if param in safe_kwargs:
                safe_kwargs[param] = "******"
        
        # 获取参数名称
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # 构建args的字典表示
        args_dict = {}
        for i, arg in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                if param_name in sensitive_params:
                    args_dict[param_name] = "******"
                else:
                    args_dict[param_name] = arg
            else:
                args_dict[f"arg{i}"] = arg
        
        context["args"] = args_dict
        context["kwargs"] = safe_kwargs
        
    return context

def _handle_exception(
    e: Exception,
    context: Dict[str, Any],
    logger: logging.Logger,
    message: str,
    level: int,
    include_traceback: bool
) -> None:
    """
    处理和记录异常
    
    统一处理异常记录逻辑。
    
    Args:
        e: 捕获的异常
        context: 日志上下文
        logger: 日志记录器
        message: 日志消息模板
        level: 日志级别
        include_traceback: 是否包含堆栈跟踪
    """
    # 添加错误信息到上下文
    context["error"] = str(e)
    context["error_type"] = e.__class__.__name__
    
    # 格式化并记录错误日志
    try:
        log_msg = message.format(**context)
    except KeyError:
        log_msg = f"执行{context['function_name']}时发生错误: {str(e)}"
    
    if include_traceback:
        logger.exception(log_msg, extra=context)
    else:
        logger.log(level, log_msg, extra=context)

def log_exception(
    logger: Optional[logging.Logger] = None,
    level: Optional[int] = None,
    message: Optional[str] = None,
    include_traceback: Optional[bool] = None,
    sensitive_params: Optional[List[str]] = None
) -> Callable:
    """
    异常日志装饰器
    
    记录函数执行过程中发生的异常，并继续向上传播异常。
    
    Args:
        logger: 用于记录日志的Logger实例，不指定则使用函数所在模块的logger
        level: 日志级别，不指定则使用配置默认值
        message: 自定义错误消息，支持格式化，可用变量：
                {function_name}, {error}, {error_type}, {args}, {kwargs}, {module}
        include_traceback: 是否包含完整堆栈跟踪，不指定则使用配置默认值
        sensitive_params: 敏感参数名称列表，这些参数值将被隐藏
        
    Returns:
        Callable: 装饰器函数
        
    Notes:
        - 自动捕获并记录所有类型的异常
        - 异常被记录后会继续抛出，不会被吞没
        - 记录异常时包含函数名称、参数等上下文信息
        
    Example:
        @log_exception()
        async def risky_function(param1, param2):
            # 可能抛出异常的代码
            ...
            
        @log_exception(level=logging.ERROR, message="自定义异常消息: {error}")
        async def complex_operation(data):
            # 复杂操作
    """
    # 获取配置
    config = get_config().logging
    
    # 使用传入参数或配置默认值
    _level = level if level is not None else config.error_log_level
    _include_traceback = include_traceback if include_traceback is not None else config.log_exceptions
    _sensitive_params = sensitive_params if sensitive_params is not None else config.sensitive_params
    _message = message if message is not None else "执行{function_name}时发生错误: {error}"
    
    def decorator(func: Callable) -> Callable:
        # 确定使用的logger
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
            
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 构建日志上下文
            context = _build_log_context(func, args, kwargs, _sensitive_params, config)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_exception(e, context, logger, _message, _level, _include_traceback)
                raise
                
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 构建日志上下文
            context = _build_log_context(func, args, kwargs, _sensitive_params, config)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_exception(e, context, logger, _message, _level, _include_traceback)
                raise
        
        # 根据函数类型返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator 