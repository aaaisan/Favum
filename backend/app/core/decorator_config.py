"""
装饰器配置模块

提供全局装饰器配置和默认值设置，使装饰器更加灵活和可配置。
"""

from typing import Dict, Any, Optional, List
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
import logging

# 日志装饰器配置
class LoggingConfig(BaseModel):
    """日志装饰器配置"""
    
    # 日志级别配置
    default_log_level: int = logging.INFO
    error_log_level: int = logging.ERROR
    
    # 是否记录函数参数
    log_args: bool = True
    
    # 是否记录函数返回值
    log_return: bool = False
    
    # 是否记录异常详情
    log_exceptions: bool = True
    
    # 默认日志格式
    log_format: str = "{function_name} 执行时间: {execution_time:.3f}s"
    
    # 是否使用结构化日志
    structured_logging: bool = True
    
    # 敏感参数名称列表，这些参数值将被隐藏
    sensitive_params: List[str] = ["password", "token", "secret", "key", "auth"]

# 缓存装饰器配置
class CacheConfig(BaseModel):
    """缓存装饰器配置"""
    
    # 默认过期时间（秒）
    default_expire: int = 300
    
    # 是否启用缓存
    enabled: bool = True
    
    # 最大缓存项数
    max_size: int = 1000
    
    # 是否使用LRU缓存策略
    use_lru: bool = True
    
    # 自定义键生成函数名称
    key_builder: Optional[str] = None
    
    # 是否在背景中更新过期缓存
    background_refresh: bool = False

# 异常处理装饰器配置
class ExceptionHandlerConfig(BaseModel):
    """异常处理装饰器配置"""
    
    # 是否重新抛出异常
    reraise: bool = False
    
    # 是否记录异常堆栈
    log_traceback: bool = True
    
    # 默认HTTP状态码
    default_status_code: int = 500
    
    # 默认错误消息
    default_message: str = "操作失败"
    
    # 自定义错误处理函数名称
    error_handler: Optional[str] = None
    
    # 是否返回详细错误信息
    include_details: bool = False

# 重试装饰器配置
class RetryConfig(BaseModel):
    """重试装饰器配置"""
    
    # 最大重试次数
    max_retries: int = 3
    
    # 重试延迟（秒）
    delay: float = 1.0
    
    # 延迟是否增加（指数退避）
    backoff: bool = True
    
    # 延迟因子（用于指数退避）
    backoff_factor: float = 2.0
    
    # 最大延迟（秒）
    max_delay: float = 60.0
    
    # 可重试的异常类型，为空则重试所有异常
    retry_exceptions: List[str] = []
    
    # 重试之前是否记录日志
    log_before_retry: bool = True

# 速率限制装饰器配置
class RateLimitConfig(BaseModel):
    """速率限制装饰器配置"""
    
    # 默认请求限制数
    default_limit: int = 100
    
    # 默认时间窗口（秒）
    default_window: int = 3600
    
    # 是否启用
    enabled: bool = True
    
    # 超出限制的响应状态码
    status_code: int = 429
    
    # 超出限制的响应消息
    message: str = "请求频率过高，请稍后再试"
    
    # 是否在响应头中包含速率限制信息
    include_headers: bool = True
    
    # 是否对不同IP应用不同限制
    per_ip: bool = True

# 全局装饰器配置
class DecoratorConfig(BaseModel):
    """全局装饰器配置"""
    
    # 是否全局启用所有装饰器
    enabled: bool = True
    
    # 日志装饰器配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # 缓存装饰器配置
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    # 异常处理装饰器配置
    exception_handler: ExceptionHandlerConfig = Field(default_factory=ExceptionHandlerConfig)
    
    # 重试装饰器配置
    retry: RetryConfig = Field(default_factory=RetryConfig)
    
    # 速率限制装饰器配置
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

# 创建默认配置实例
decorator_config = DecoratorConfig()

def get_config() -> DecoratorConfig:
    """获取当前装饰器配置"""
    return decorator_config

def update_config(config_dict: Dict[str, Any]) -> None:
    """更新装饰器配置
    
    Args:
        config_dict: 配置字典，格式为 {"section.key": value}
            例如：{"logging.log_args": False, "cache.enabled": False}
    """
    global decorator_config
    
    for key, value in config_dict.items():
        if "." in key:
            section, option = key.split(".", 1)
            if hasattr(decorator_config, section):
                section_config = getattr(decorator_config, section)
                if hasattr(section_config, option):
                    setattr(section_config, option, value)
                else:
                    raise ValueError(f"未知配置选项: {key}")
        else:
            if hasattr(decorator_config, key):
                setattr(decorator_config, key, value)
            else:
                raise ValueError(f"未知配置选项: {key}")

def reset_config() -> None:
    """重置装饰器配置为默认值"""
    global decorator_config
    decorator_config = DecoratorConfig() 