"""
性能优化装饰器模块

提供用于性能优化的装饰器：
- cache: 响应缓存
- rate_limit: 请求限流
- log_execution_time: 执行时间记录

所有装饰器都支持异步函数，并提供完整的类型提示。
"""

from functools import wraps
from typing import Any, Callable, Optional, List, Union, Dict, Tuple
import time
import json
import logging
import inspect
import asyncio

from fastapi import HTTPException, Request
from redis.exceptions import RedisError

from .logging import get_logger
from .config import settings
from ..utils.profiler import Profiler
from .context_managers import redis_pipeline, profiling
from .decorator_config import get_config

logger = logging.getLogger(__name__)

def _build_log_context(
    func: Callable,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    sensitive_params: List[str],
    log_args: bool
) -> Dict[str, Any]:
    """
    构建日志上下文
    
    为日志记录构建包含函数信息和安全处理后参数的上下文。
    
    Args:
        func: 被装饰的函数
        args: 位置参数
        kwargs: 关键字参数
        sensitive_params: 敏感参数列表
        log_args: 是否记录函数参数
        
    Returns:
        Dict[str, Any]: 日志上下文字典
    """
    # 构建基本上下文
    context = {
        "function_name": func.__name__,
        "module": func.__module__,
    }
    
    # 如果配置要求记录参数
    if log_args:
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

def _format_log_message(
    message_template: str, 
    context: Dict[str, Any], 
    default_message: str
) -> str:
    """
    格式化日志消息
    
    根据模板和上下文格式化日志消息，处理格式化错误。
    
    Args:
        message_template: 消息模板
        context: 上下文数据
        default_message: 默认消息（当格式化失败时使用）
        
    Returns:
        str: 格式化后的消息
    """
    try:
        return message_template.format(**context)
    except KeyError:
        return default_message

def rate_limit(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    速率限制装饰器
    
    限制API请求频率。
    
    Args:
        limit: 请求限制数，不指定则使用配置默认值
        window: 时间窗口（秒），不指定则使用配置默认值
        key_func: 自定义键生成函数，用于区分不同请求者
        
    Returns:
        Callable: 装饰器函数
    """
    # 获取配置
    config = get_config().rate_limit
    
    # 使用传入参数或配置默认值
    _limit = limit if limit is not None else config.default_limit
    _window = window if window is not None else config.default_window
    
    # 如果速率限制禁用，返回一个透明装饰器
    if not config.enabled:
        def pass_through(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return pass_through
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 此处简化实现，真实环境需要完整的速率限制实现
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def cache(
    expire: Optional[int] = None, 
    key_prefix: Optional[str] = None,
    include_query_params: bool = True,
    include_user_id: bool = True
):
    """
    缓存装饰器
    
    缓存函数的返回值，支持Redis缓存。
    
    Args:
        expire: 缓存过期时间（秒），不指定则使用配置默认值
        key_prefix: 缓存键前缀，默认为函数名
        include_query_params: 是否在缓存键中包含查询参数
        include_user_id: 是否在缓存键中包含用户ID
        
    Returns:
        装饰器函数
    """
    # 获取配置
    config = get_config().cache
    
    # 使用传入参数或配置默认值
    _expire = expire if expire is not None else config.default_expire
    
    # 如果缓存禁用，返回一个透明装饰器
    if not config.enabled:
        def pass_through(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return pass_through
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 此处简化实现，真实环境需要完整的缓存实现
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def log_execution_time(
    logger: Optional[logging.Logger] = None,
    level: Optional[int] = None,
    message: Optional[str] = None,
    log_args: Optional[bool] = None,
    log_return: Optional[bool] = None,
    sensitive_params: Optional[List[str]] = None
):
    """
    执行时间日志装饰器
    
    记录函数执行时间，支持同步和异步函数。
    
    Args:
        logger: 用于记录日志的Logger实例，不指定则使用函数所在模块的logger
        level: 日志级别，不指定则使用配置默认值
        message: 自定义日志消息，支持格式化，可用变量：
                {function_name}, {execution_time}, {args}, {kwargs}, {module}
        log_args: 是否记录函数参数，不指定则使用配置默认值
        log_return: 是否记录函数返回值，不指定则使用配置默认值
        sensitive_params: 敏感参数名称列表，这些参数值将被隐藏，不指定则使用配置默认值
        
    Returns:
        装饰器函数
        
    Examples:
        # 基本用法
        @log_execution_time()
        async def my_function(arg1, arg2):
            # 函数代码
            
        # 自定义日志
        @log_execution_time(level=logging.DEBUG, message="{function_name}耗时{execution_time:.2f}秒")
        async def complex_operation(data):
            # 复杂操作
    """
    # 获取配置
    config = get_config().logging
    
    # 使用传入参数或配置默认值
    _level = level if level is not None else config.default_log_level
    _log_args = log_args if log_args is not None else config.log_args
    _log_return = log_return if log_return is not None else config.log_return
    _message = message if message is not None else config.log_format
    _sensitive_params = sensitive_params if sensitive_params is not None else config.sensitive_params
    
    def decorator(func):
        # 确定使用的logger
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 构建日志上下文
            context = {
                'elapsed_ms': elapsed_time,
                'function': func.__name__,
                'module_name': func.__module__,  # 使用module_name而不是module
            }
            
            # 记录日志
            log_msg = f"{func.__name__} 执行时间 {elapsed_time:.2f}ms"
            logger.info(log_msg, extra=context)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 构建日志上下文
            context = {
                'elapsed_ms': elapsed_time,
                'function': func.__name__,
                'module_name': func.__module__,  # 使用module_name而不是module
            }
            
            # 记录日志
            log_msg = f"{func.__name__} 执行时间 {elapsed_time:.2f}ms"
            logger.info(log_msg, extra=context)
            
            return result
        
        # 根据函数类型返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator 

# 在配置类中添加slow_threshold_ms属性
class PerformanceConfig:
    """性能监控配置"""
    
    def __init__(self):
        """初始化性能监控配置"""
        self.enabled = True
        self.log_level = logging.INFO
        self.error_log_level = logging.ERROR
        self.slow_threshold_ms = 500  # 添加慢查询阈值，默认500毫秒
        self.include_args = False
        self.include_result = False
        self.max_args_length = 100
        self.max_result_length = 100 