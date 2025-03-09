import logging
from typing import Any, Dict, Optional, Type
# from typing import Any, Callable, Dict, Optional, Type
from fastapi import Request
from uuid import uuid4
# from ..core.decorators.logging import log_execution_time  # 从decorators包导入装饰器
# from ..core.decorators.logging import log_exception, log_execution_time  # 从decorators包导入装饰器

class RequestContextFilter(logging.Filter):
    """请求上下文过滤器，用于添加请求相关信息到日志记录"""
    
    def __init__(self, request: Optional[Request] = None):
        """初始化过滤器"""
        super().__init__()
        self.request = request
        self.request_id = str(uuid4())
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求相关信息到日志记录"""
        if self.request and not hasattr(record, 'request_id'):
            record.request_id = getattr(self.request.state, 'request_id', 'unknown')
        return True

def get_logger(name: str) -> logging.Logger:
    """获取带有默认配置的日志记录器"""
    logger = logging.getLogger(name)
    return logger

# log_exception 和 log_execution_time 装饰器已移动到 core
# 请从 core.decorators 导入

class LoggerMixin:
    """日志混入类，为类添加日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__module__)
        return self._logger
    
    def log_method_call(self, method_name: str, **kwargs: Any) -> None:
        """记录方法调用"""
        self.logger.debug(
            f"调用方法 {method_name}",
            extra={
                "class": self.__class__.__name__,
                "method": method_name,
                "params": kwargs
            }
        )

# 使用示例：
# @log_exception()
# @log_execution_time()
# async def some_function():
#     pass
#
# class SomeClass(LoggerMixin):
#     def some_method(self):
#         self.log_method_call("some_method", param1="value1")
#         self.logger.info("执行某些操作") 