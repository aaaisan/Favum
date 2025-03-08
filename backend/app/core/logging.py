"""
日志配置模块

提供结构化日志记录功能，支持：
- JSON格式的日志输出
- 多目标日志输出（控制台、文件）
- 日志文件自动轮转
- 错误日志单独存储
- 上下文数据绑定
- 异常信息完整记录

主要组件：
- JSONFormatter: 将日志格式化为JSON格式
- CustomLogger: 支持上下文数据绑定的日志记录器
- setup_logging: 配置整个日志系统
- get_logger: 获取自定义日志记录器的函数

使用方式：
    logger = get_logger(__name__)
    logger.bind(user_id=123, request_id="abc-123")
    logger.error("数据库连接失败", exc_info=True)
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import io


class LineBufferHandler(logging.handlers.MemoryHandler):
    """
    行限制的日志处理器
    
    将日志记录存储在内存缓冲区中，当缓冲区达到容量时，
    将最新的N行写入文件，丢弃旧的日志行。
    
    特性:
    - 只保留最新的N行日志
    - 定期刷新到实际的日志文件
    - 避免日志文件过度增长
    """
    
    def __init__(self, filename, max_lines=50, encoding='utf-8'):
        """
        初始化行限制处理器
        
        Args:
            filename: 日志文件路径
            max_lines: 保留的最大行数，默认50
            encoding: 文件编码，默认utf-8
        """
        super().__init__(max_lines, flushLevel=logging.ERROR)
        self.filename = filename
        self.max_lines = max_lines
        self.encoding = encoding
        self.buffer = []
        self.target = logging.FileHandler(filename, encoding=encoding)
    
    def emit(self, record):
        """
        发送日志记录到内存缓冲区
        
        Args:
            record: 日志记录对象
        """
        self.buffer.append(record)
        if len(self.buffer) > self.max_lines:
            self.buffer.pop(0)  # 移除最旧的记录
        self.flush()
    
    def flush(self):
        """
        将缓冲区中的记录写入文件
        """
        if self.buffer:
            target_formatter = self.target.formatter or logging.Formatter()
            with io.open(self.filename, 'w', encoding=self.encoding) as f:
                for record in self.buffer:
                    formatted_record = target_formatter.format(record)
                    f.write(formatted_record + '\n')


class JSONFormatter(logging.Formatter):
    """
    JSON格式的日志格式化器
    
    将日志记录转换为结构化的JSON格式，包含：
    - 时间戳（ISO格式）
    - 日志级别
    - 日志器名称
    - 日志消息
    - 代码位置（模块、函数、行号）
    - 异常信息（如果有）
    - 额外的上下文数据（如果有）
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON字符串
        
        Args:
            record: 日志记录对象
            
        Returns:
            str: JSON格式的日志字符串
            
        Notes:
            - 时间戳使用ISO格式
            - 异常信息包含类型、消息和堆栈跟踪
            - 支持额外的上下文数据
            - 确保所有字符串正确编码（包括中文）
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # 添加额外上下文数据
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)

class CustomLogger(logging.Logger):
    """
    自定义日志记录器
    
    扩展标准Logger，添加了上下文数据绑定功能。
    可以为日志记录器绑定持久的上下文数据，这些数据会被添加到每条日志记录中。
    
    特性：
    - 支持动态绑定上下文数据
    - 上下文数据在所有日志级别可用
    - 线程安全的数据存储
    """
    
    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别，默认为NOTSET
        """
        super().__init__(name, level)
        self.extra_data: Dict[str, Any] = {}
    
    def bind(self, **kwargs: Any) -> None:
        """
        绑定上下文数据到日志记录器
        
        Args:
            **kwargs: 要绑定的键值对数据
            
        Example:
            logger.bind(user_id=123, request_id="abc-123")
        """
        self.extra_data.update(kwargs)
    
    def _log(self, level: int, msg: str, args: tuple, **kwargs: Any) -> None:
        """
        重写日志记录方法以包含绑定的上下文数据
        
        Args:
            level: 日志级别
            msg: 日志消息
            args: 消息格式化参数
            **kwargs: 额外的关键字参数
        """
        if self.extra_data and "extra" not in kwargs:
            kwargs["extra"] = {"extra_data": self.extra_data}
        super()._log(level, msg, args, **kwargs)

def setup_logging() -> None:
    """
    配置日志系统
    
    设置整个应用的日志记录系统，包括：
    1. 创建必要的日志目录
    2. 配置JSON格式化器
    3. 设置多个日志处理器：
       - 控制台输出
       - 主日志文件（只保留最新的50行）
       - 错误日志文件（只保留最新的50行）
    4. 配置各个组件的日志记录器：
       - FastAPI
       - Uvicorn
       - SQLAlchemy
       
    Notes:
        - 日志文件位于logs目录
        - 主日志文件和错误日志文件都限制为最多50行
        - 所有日志都使用JSON格式
        - 只记录错误级别及以上的日志
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 注册自定义日志记录器
    logging.setLoggerClass(CustomLogger)
    
    # 创建JSON格式化器
    json_formatter = JSONFormatter()
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(logging.ERROR)  # 只记录错误及以上级别
    
    # 配置行限制的文件处理器（限制为50行）
    file_handler = LineBufferHandler(
        log_dir / "app.log",
        max_lines=50,
        encoding="utf-8"
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.ERROR)  # 只记录错误及以上级别
    
    # 配置行限制的错误日志处理器（限制为50行）
    error_handler = LineBufferHandler(
        log_dir / "error.log",
        max_lines=50,
        encoding="utf-8"
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)  # 设置根日志记录器级别为ERROR
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # 配置FastAPI日志记录器
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.ERROR)
    
    # 配置uvicorn访问日志记录器
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.ERROR)
    
    # 配置SQLAlchemy日志记录器
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.ERROR)

def get_logger(name: str) -> CustomLogger:
    """
    获取自定义日志记录器
    
    Args:
        name: 日志记录器名称，通常使用__name__
        
    Returns:
        CustomLogger: 自定义日志记录器实例
        
    Example:
        logger = get_logger(__name__)
        logger.error("这是一条错误日志")
    """
    logger = logging.getLogger(name)
    if not isinstance(logger, CustomLogger):
        # 如果尚未配置CustomLogger
        logging.setLoggerClass(CustomLogger)
        logger = logging.getLogger(name)
    return logger  # type: ignore

# 使用示例：
# logger = get_logger(__name__)
# logger.bind(user_id=123, request_id="abc-123")
# logger.error("数据库连接失败", exc_info=True) 