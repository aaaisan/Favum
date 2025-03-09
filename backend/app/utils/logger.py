"""
日志工具模块

提供统一的日志记录函数，便于在应用中进行标准化的日志记录。
这些函数增强了基本日志记录，添加了额外的上下文信息。
"""

from datetime import datetime
from typing import Any, Optional
# from typing import Any, Dict, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)

def log_error(
    message: str, 
    exception: Optional[Exception] = None, 
    **extra: Any
) -> None:
    """统一的错误日志记录函数
    
    记录错误信息，并添加额外的上下文数据。
    如果提供了异常对象，会包含异常类型和详细信息。
    
    Args:
        message: 错误消息
        exception: 异常对象（可选）
        **extra: 额外的上下文信息
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        **extra
    }
    
    if exception:
        log_data.update({
            "error_type": exception.__class__.__name__,
            "error_details": str(exception)
        })
        
    logger.error(
        message if not exception else f"{message}: {str(exception)}",
        extra=log_data
    )

def log_warning(
    message: str, 
    **extra: Any
) -> None:
    """统一的警告日志记录函数
    
    记录警告信息，并添加额外的上下文数据。
    
    Args:
        message: 警告消息
        **extra: 额外的上下文信息
    """
    logger.warning(
        message,
        extra={
            "timestamp": datetime.now().isoformat(),
            **extra
        }
    )

def log_info(
    message: str, 
    **extra: Any
) -> None:
    """统一的信息日志记录函数
    
    记录普通信息，并添加额外的上下文数据。
    
    Args:
        message: 信息消息
        **extra: 额外的上下文信息
    """
    logger.info(
        message,
        extra={
            "timestamp": datetime.now().isoformat(),
            **extra
        }
    )

def log_debug(
    message: str, 
    **extra: Any
) -> None:
    """统一的调试日志记录函数
    
    记录调试信息，并添加额外的上下文数据。
    
    Args:
        message: 调试消息
        **extra: 额外的上下文信息
    """
    logger.debug(
        message,
        extra={
            "timestamp": datetime.now().isoformat(),
            **extra
        }
    )

def log_critical(
    message: str, 
    exception: Optional[Exception] = None, 
    **extra: Any
) -> None:
    """统一的严重错误日志记录函数
    
    记录严重错误信息，并添加额外的上下文数据。
    如果提供了异常对象，会包含异常类型和详细信息。
    
    Args:
        message: 错误消息
        exception: 异常对象（可选）
        **extra: 额外的上下文信息
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        **extra
    }
    
    if exception:
        log_data.update({
            "error_type": exception.__class__.__name__,
            "error_details": str(exception)
        })
        
    logger.critical(
        message if not exception else f"{message}: {str(exception)}",
        extra=log_data
    )

def log_api_call(
    request_method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """记录API调用
    
    提供完整的API调用记录，包括请求方法、端点、状态码、执行时间等。
    
    Args:
        request_method: HTTP请求方法
        endpoint: API端点
        status_code: HTTP状态码
        duration_ms: 执行时间（毫秒）
        user_id: 用户ID（可选）
        error: 错误信息（可选）
    """
    log_data = {
        "request_method": request_method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if error:
        log_data["error"] = error
        logger.error(f"API调用失败: {endpoint}", extra=log_data)
    else:
        level = "warning" if duration_ms > 1000 else "info"
        getattr(logger, level)(f"API调用: {endpoint}", extra=log_data)

def log_db_operation(
    operation: str,
    model: str,
    duration_ms: float,
    record_count: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """记录数据库操作
    
    提供完整的数据库操作记录，包括操作类型、模型、执行时间等。
    
    Args:
        operation: 操作类型（select, insert, update, delete等）
        model: 数据模型名称
        duration_ms: 执行时间（毫秒）
        record_count: 影响的记录数（可选）
        error: 错误信息（可选）
    """
    log_data = {
        "operation": operation,
        "model": model,
        "duration_ms": duration_ms
    }
    
    if record_count is not None:
        log_data["record_count"] = record_count
    
    if error:
        log_data["error"] = error
        logger.error(f"数据库操作失败: {operation} {model}", extra=log_data)
    else:
        level = "warning" if duration_ms > 100 else "debug"
        getattr(logger, level)(f"数据库操作: {operation} {model}", extra=log_data) 