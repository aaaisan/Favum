"""
装饰器集合

此包包含所有应用装饰器，按功能分类：

认证装饰器 (auth.py):
- validate_token: 验证JWT令牌
- require_permissions: 检查用户权限
- require_roles: 检查用户角色
- owner_required: 检查资源所有权

缓存装饰器 (cache.py):
- memo: 内存缓存
- async_memo: 异步函数内存缓存
- timed_memo: 带过期时间的内存缓存
- typed_memo: 类型敏感的内存缓存

错误处理装饰器 (error.py):
- handle_exceptions: 统一异常处理
- retry: 自动重试函数执行

日志装饰器 (logging.py):
- log_execution_time: 记录函数执行时间
- log_exception: 记录异常日志

性能装饰器 (performance.py):
- rate_limit: 请求限流
- cache: 响应缓存
- endpoint_rate_limit: 端点级限流

上下文管理器 (context.py):
- redis_pipeline: Redis管道上下文
- profiling: 性能分析上下文
- transaction: 数据库事务上下文
- error_boundary: 错误边界上下文
- request_context: 请求上下文

API装饰器组合 (api_decorators.py):
- admin_endpoint: 管理员端点装饰器组合
- moderator_endpoint: 版主端点装饰器组合
- public_endpoint: 公共端点装饰器组合
- owner_endpoint: 资源所有者端点装饰器组合
"""

# 为保持向后兼容性，从各个模块导入所有装饰器
from .auth import (
    validate_token,
    require_permissions,
    require_roles,
    owner_required
)

from .cache import (
    memo,
    async_memo,
    timed_memo,
    typed_memo
)

from .error import (
    handle_exceptions,
    retry
)

from .logging import (
    log_execution_time,
    log_exception
)

from .performance import (
    rate_limit,
    cache,
    endpoint_rate_limit
)

from .context import (
    redis_pipeline,
    profiling,
    transaction,
    error_boundary,
    request_context
)

from .api_decorators import (
    admin_endpoint,
    moderator_endpoint,
    public_endpoint,
    owner_endpoint
)

# 导出所有公开API
__all__ = [
    # 认证装饰器
    'validate_token', 'require_permissions', 'require_roles', 'owner_required',
    
    # 缓存装饰器
    'memo', 'async_memo', 'timed_memo', 'typed_memo',
    
    # 错误处理装饰器
    'handle_exceptions', 'retry', 'with_error_handling'
    
    # 日志装饰器
    'log_execution_time', 'log_exception',
    
    # 性能装饰器
    'rate_limit', 'cache', 'endpoint_rate_limit',
    
    # 上下文管理器
    'redis_pipeline', 'profiling', 'transaction', 'error_boundary', 'request_context',
    
    # API装饰器组合
    'admin_endpoint', 'moderator_endpoint', 'public_endpoint', 'owner_endpoint'
] 