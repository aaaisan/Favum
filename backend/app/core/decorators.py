"""
装饰器模块

提供一组功能强大的装饰器，用于增强API端点和服务方法的功能：

认证与授权：
- validate_token: Token验证
- require_permissions: 权限检查
- require_roles: 角色检查
- owner_required: 资源所有者验证

性能与可靠性：
- cache: 响应缓存
- rate_limit: 请求限流
- retry: 自动重试
- log_execution_time: 执行时间记录
- log_exception: 异常日志记录

错误处理：
- handle_exceptions: 统一异常处理

内存缓存：
- memo: 基本内存缓存装饰器
- async_memo: 异步函数的内存缓存装饰器
- timed_memo: 带过期时间的内存缓存装饰器
- typed_memo: 类型敏感的内存缓存装饰器

上下文管理器：
- redis_pipeline: Redis管道操作上下文
- profiling: 性能分析上下文
- transaction: 数据库事务上下文
- error_boundary: 错误处理边界上下文
- request_context: 请求上下文

所有装饰器和上下文管理器都支持异步函数，并提供完整的类型提示。

注意：此模块导入并重新导出了单独装饰器文件中的装饰器，
以保持向后兼容性。建议在新代码中直接从专用模块导入。
"""

# 导入认证相关装饰器
from .auth_decorators import (
    validate_token,
    require_permissions,
    require_roles,
    owner_required
)

# 导入性能相关装饰器
from .performance_decorators import (
    cache,
    rate_limit,
    log_execution_time
)

# 导入错误处理相关装饰器
from .error_decorators import (
    handle_exceptions,
    retry
)

# 导入内存缓存装饰器
from .cache_decorators import (
    memo,
    async_memo,
    timed_memo,
    typed_memo
)

# 导入上下文管理器
from .context_managers import (
    redis_pipeline,
    profiling,
    transaction,
    error_boundary,
    request_context
)

# 导入日志装饰器 - 从 utils 移至 core
from .logging_decorators import (
    log_exception
)

# 为保持向后兼容性，重新导出所有装饰器和上下文管理器
__all__ = [
    # 认证相关
    'validate_token',
    'require_permissions',
    'require_roles',
    'owner_required',
    
    # 性能相关
    'cache',
    'rate_limit',
    'log_execution_time',
    
    # 错误处理相关
    'handle_exceptions',
    'retry',
    
    # 内存缓存相关
    'memo',
    'async_memo',
    'timed_memo',
    'typed_memo',
    
    # 日志相关
    'log_exception',
    
    # 上下文管理器
    'redis_pipeline',
    'profiling',
    'transaction',
    'error_boundary',
    'request_context'
] 