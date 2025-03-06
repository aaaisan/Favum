"""
上下文管理器装饰器

提供各种上下文管理的装饰器：
- redis_pipeline: Redis管道操作上下文
- profiling: 性能分析上下文
- transaction: 数据库事务上下文
- error_boundary: 错误处理边界上下文
- request_context: 请求上下文
"""

from contextlib import contextmanager, asynccontextmanager
from functools import wraps
from typing import TypeVar, Callable, Dict, Any, Optional, Generator, AsyncGenerator
import inspect
import time
import traceback
import cProfile
import pstats
import io
from ...core.logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)

T = TypeVar('T')

@contextmanager
def redis_pipeline(redis_client):
    """
    Redis管道上下文管理器
    
    创建一个Redis管道，用于批量执行Redis命令。
    
    Args:
        redis_client: Redis客户端实例
        
    Yields:
        Pipeline: Redis管道对象
    """
    pipeline = redis_client.pipeline()
    try:
        yield pipeline
        pipeline.execute()
    except Exception as e:
        logger.error(f"Redis管道执行失败: {str(e)}")
        pipeline.reset()
        raise

@contextmanager
def profiling(
    sort_by: str = 'cumulative',
    limit: int = 20,
    output_file: Optional[str] = None
):
    """
    性能分析上下文管理器
    
    对代码块进行性能分析，可以输出到文件或返回分析结果。
    
    Args:
        sort_by: 排序方式，默认按累计时间排序
        limit: 显示的结果数量限制
        output_file: 输出文件路径，不提供则返回字符串结果
        
    Yields:
        None: 无返回值，只执行上下文中的代码并分析
    """
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        
        # 创建统计对象
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
        stats.print_stats(limit)
        
        # 输出结果
        if output_file:
            with open(output_file, 'w') as f:
                f.write(s.getvalue())
            logger.info(f"性能分析结果已保存到: {output_file}")
        else:
            logger.info(f"性能分析结果:\n{s.getvalue()}")

@contextmanager
def transaction(db_session: Session):
    """
    数据库事务上下文管理器
    
    创建一个事务边界，自动提交或回滚事务。
    
    Args:
        db_session: SQLAlchemy会话对象
        
    Yields:
        Session: 数据库会话对象
    """
    try:
        yield db_session
        db_session.commit()
        logger.debug("事务已提交")
    except Exception as e:
        db_session.rollback()
        logger.error(f"事务已回滚，原因: {str(e)}")
        raise

@asynccontextmanager
async def error_boundary(
    error_handler: Optional[Callable[[Exception], Any]] = None,
    log_error: bool = True,
    reraise: bool = True
):
    """
    错误处理边界上下文管理器
    
    捕获上下文中的异常，提供统一的错误处理机制。
    
    Args:
        error_handler: 错误处理函数，接收异常对象作为参数
        log_error: 是否记录异常日志，默认True
        reraise: 是否重新抛出异常，默认True
        
    Yields:
        None: 无返回值，只执行上下文中的代码并处理异常
    """
    try:
        yield
    except Exception as e:
        # 记录异常日志
        if log_error:
            logger.error(
                f"错误边界捕获到异常: {type(e).__name__}: {str(e)}\n"
                f"{traceback.format_exc()}"
            )
        
        # 调用错误处理函数
        if error_handler:
            try:
                error_handler(e)
            except Exception as handler_error:
                logger.error(f"错误处理器执行失败: {str(handler_error)}")
        
        # 重新抛出异常
        if reraise:
            raise

@contextmanager
def request_context(request_id: str, user_id: Optional[str] = None):
    """
    请求上下文管理器
    
    在当前执行上下文中存储请求相关信息，便于日志记录和追踪。
    
    Args:
        request_id: 请求ID
        user_id: 用户ID，可选
        
    Yields:
        Dict[str, Any]: 上下文信息字典
    """
    # 创建上下文信息
    context = {
        "request_id": request_id,
        "start_time": time.time(),
        "user_id": user_id
    }
    
    # 设置日志上下文
    old_factory = logger.makeRecord
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        if user_id:
            record.user_id = user_id
        return record
    
    logger.makeRecord = record_factory
    
    try:
        yield context
    finally:
        # 恢复原始日志工厂
        logger.makeRecord = old_factory
        
        # 记录请求完成信息
        execution_time = time.time() - context["start_time"]
        logger.info(f"请求处理完成，耗时: {execution_time:.6f}秒", extra={
            "request_id": request_id,
            "user_id": user_id,
            "execution_time": execution_time
        }) 