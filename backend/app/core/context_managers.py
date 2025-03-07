"""
上下文管理器模块

提供一组可复用的上下文管理器，便于资源管理、性能分析、错误处理和跨函数上下文共享。
所有上下文管理器都支持同步和异步操作。
"""

import time
import logging
import traceback
import contextvars
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast
from contextlib import contextmanager, asynccontextmanager

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

# 创建请求上下文变量
request_id = contextvars.ContextVar('request_id', default=None)
current_user = contextvars.ContextVar('current_user', default=None)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def redis_pipeline(redis: Redis, raise_on_error: bool = True):
    """
    Redis管道上下文管理器
    
    提供异步Redis管道操作上下文，自动处理管道执行和异常。
    
    Args:
        redis: Redis客户端实例
        raise_on_error: 是否在出错时抛出异常
        
    Yields:
        Redis管道对象
        
    Raises:
        RedisError: 如果raise_on_error为True且操作失败时
        
    Example:
        ```python
        async with redis_pipeline(redis_client) as pipe:
            pipe.set("key1", "value1")
            pipe.set("key2", "value2")
            # 退出上下文时自动执行
        ```
    """
    pipeline = redis.pipeline()
    try:
        yield pipeline
        await pipeline.execute()
    except RedisError as e:
        logger.error(f"Redis管道操作失败: {str(e)}")
        if raise_on_error:
            raise
    finally:
        # 确保关闭连接
        await pipeline.reset()

@contextmanager
def profiling(operation_name: str, threshold_ms: Optional[float] = None):
    """
    性能分析上下文管理器
    
    用于测量代码块的执行时间并记录日志。
    
    Args:
        operation_name: 操作名称，用于日志标识
        threshold_ms: 日志记录阈值(毫秒)，仅记录超过此阈值的操作
        
    Yields:
        包含执行信息的字典
        
    Example:
        ```python
        with profiling("数据库查询", threshold_ms=100) as stats:
            # 执行需要测量性能的代码
            result = expensive_operation()
            stats["rows_count"] = len(result)  # 可以添加自定义指标
            
        # 如果操作耗时超过100ms，会记录日志
        ```
    """
    start_time = time.time()
    stats = {"start_time": start_time, "execution_time_ms": 0}
    
    try:
        yield stats
    finally:
        execution_time_ms = (time.time() - start_time) * 1000
        stats["execution_time_ms"] = execution_time_ms
        
        if threshold_ms is None or execution_time_ms > threshold_ms:
            # 构建日志消息，包含自定义属性
            log_message = f"{operation_name}: {execution_time_ms:.2f}ms"
            custom_attrs = ", ".join(
                f"{k}={v}" for k, v in stats.items() 
                if k not in ["start_time", "execution_time_ms"]
            )
            if custom_attrs:
                log_message += f" ({custom_attrs})"
                
            logger.info(log_message)

@asynccontextmanager
async def transaction(session: AsyncSession, autocommit: bool = True):
    """
    数据库事务上下文管理器
    
    提供异步数据库事务上下文，自动处理提交和回滚。
    
    Args:
        session: 数据库会话
        autocommit: 是否在退出上下文时自动提交
        
    Yields:
        数据库会话
        
    Raises:
        Exception: 任何在事务中发生的异常都会被重新抛出
        
    Example:
        ```python
        async with transaction(db_session) as session:
            user = User(name="测试用户")
            session.add(user)
            # 退出上下文时自动提交，如果出错则回滚
        ```
    """
    try:
        yield session
        if autocommit:
            await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"事务回滚: {str(e)}")
        raise
        
@contextmanager
def error_boundary(
    *exceptions: Type[Exception],
    default_value: Any = None,
    logger: Optional[logging.Logger] = None
):
    """
    错误处理边界上下文管理器
    
    用于简化异常处理，可以指定处理的异常类型和默认返回值。
    
    Args:
        *exceptions: 要捕获的异常类型，不指定则捕获所有异常
        default_value: 出现异常时返回的默认值
        logger: 用于记录异常的日志器，如不指定则使用模块日志器
        
    Yields:
        结果容器，可通过.set(value)设置正常返回值
        
    Example:
        ```python
        with error_boundary(ValueError, ZeroDivisionError, default_value=0) as result:
            value = 10 / 0  # 会捕获ZeroDivisionError
            result.set(value)  # 正常情况下设置结果
            
        print(result.value)  # 打印结果，这里会是默认值0
        ```
    """
    class ResultHolder:
        def __init__(self):
            self.value = default_value
            
        def set(self, value):
            self.value = value
            
    result = ResultHolder()
    log = logger or logging.getLogger(__name__)
    
    exceptions_to_catch = exceptions or (Exception,)
    
    try:
        yield result
    except exceptions_to_catch as e:
        trace = traceback.format_exc()
        log.error(f"捕获到异常: {str(e)}\n{trace}")
        
        # 异常情况下使用默认值
        result.value = default_value
        
@contextmanager
def request_context(**context_vars):
    """
    请求上下文管理器
    
    用于在请求范围内共享上下文信息。
    
    Args:
        **context_vars: 要存储在上下文中的键值对
        
    Yields:
        当前上下文的键值字典
        
    Example:
        ```python
        with request_context(user_id=123, is_admin=True) as ctx:
            # 现在user_id和is_admin可以在此上下文中访问
            process_request(ctx)  # 传递上下文
            
            # 也可以修改上下文
            ctx["request_start_time"] = time.time()
        ```
    """
    # 保存当前token以便恢复
    prev_tokens = {}
    tokens = {}
    context = {}
    
    # 设置上下文变量
    for key, value in context_vars.items():
        if key == 'request_id':
            prev_tokens['request_id'] = request_id.get()
            tokens['request_id'] = request_id.set(value)
        elif key == 'user':
            prev_tokens['current_user'] = current_user.get()
            tokens['current_user'] = current_user.set(value)
        
        context[key] = value
    
    try:
        yield context
    finally:
        # 恢复之前的上下文变量
        for key, token in tokens.items():
            if key == 'request_id' and 'request_id' in prev_tokens:
                request_id.reset(token)
            elif key == 'user' and 'current_user' in prev_tokens:
                current_user.reset(token) 