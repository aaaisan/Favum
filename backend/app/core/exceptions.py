from fastapi import HTTPException, status
from typing import Any, Optional, Dict, List
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

"""
自定义异常模块

定义了应用中使用的所有自定义异常类。
所有异常类都继承自APIError基类，提供了统一的错误处理机制。
每个异常类都对应特定的HTTP状态码和默认错误信息。
"""

class APIError(HTTPException):
    """
    API错误基类
    
    所有自定义API异常的基类，继承自FastAPI的HTTPException。
    提供统一的错误响应格式和处理机制。
    
    Attributes:
        status_code: HTTP状态码
        detail: 错误详细信息
        headers: 可选的响应头信息
    """
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundError(APIError):
    """
    资源未找到错误
    
    当请求的资源不存在时抛出此异常。
    
    Attributes:
        detail: 错误详细信息，默认为"资源未找到"
        status_code: HTTP 404 NOT FOUND
    """
    def __init__(self, detail: str = "资源未找到") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(APIError):
    """
    数据验证错误
    
    当请求数据未通过验证规则时抛出此异常。
    
    Attributes:
        detail: 错误详细信息，默认为"数据验证失败"
        status_code: HTTP 422 UNPROCESSABLE ENTITY
    """
    def __init__(
        self,
        detail: str = "数据验证失败",
        field_errors: Optional[Dict[str, str]] = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": detail,
                "field_errors": field_errors
            } if field_errors else detail
        )

class AuthenticationError(APIError):
    """
    认证错误
    
    当用户认证失败时抛出此异常。
    例如：无效的令牌、过期的令牌等。
    
    Attributes:
        detail: 错误详细信息，默认为"认证失败"
        status_code: HTTP 401 UNAUTHORIZED
        headers: 包含WWW-Authenticate: Bearer头
    """
    def __init__(
        self,
        detail: str = "认证失败",
        error_code: str = "authentication_failed"
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": detail,
                "error_code": error_code
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

class UserNotActivatedError(AuthenticationError):
    """
    用户未激活错误
    
    当用户账号未激活时抛出此异常。
    例如：用户注册后未验证邮箱、账号被管理员禁用等。
    
    Attributes:
        detail: 错误详细信息，默认为"请先激活您的账号"
        error_code: 固定为"user_not_activated"
        status_code: HTTP 401 UNAUTHORIZED
    """
    def __init__(self, detail: str = "请先激活您的账号") -> None:
        super().__init__(
            detail=detail,
            error_code="user_not_activated"
        )

class TokenExpiredError(AuthenticationError):
    """Token过期错误"""
    def __init__(self) -> None:
        super().__init__(
            detail="Token已过期",
            error_code="token_expired"
        )

class TokenInvalidError(AuthenticationError):
    """Token无效错误"""
    def __init__(self) -> None:
        super().__init__(
            detail="无效的Token",
            error_code="token_invalid"
        )

class TokenRevokedError(AuthenticationError):
    """Token已撤销错误"""
    def __init__(self) -> None:
        super().__init__(
            detail="Token已被撤销",
            error_code="token_revoked"
        )

class PermissionError(APIError):
    """
    权限错误
    
    当用户没有足够权限执行操作时抛出此异常。
    
    Attributes:
        detail: 错误详细信息，默认为"没有权限执行此操作"
        status_code: HTTP 403 FORBIDDEN
    """
    def __init__(
        self,
        detail: str = "没有权限执行此操作",
        required_permissions: Optional[list] = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": detail,
                "required_permissions": required_permissions
            } if required_permissions else detail
        )

class PermissionDeniedError(PermissionError):
    """权限被拒绝错误，是PermissionError的别名，提供兼容性"""
    pass

class ResourceNotFoundError(APIError):
    """资源未找到错误"""
    def __init__(
        self,
        resource_type: str,
        resource_id: Any
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"未找到{resource_type}",
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )

class ResourceConflictError(APIError):
    """资源冲突错误"""
    def __init__(
        self,
        resource_type: str,
        conflict_field: str,
        conflict_value: Any
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"{resource_type}已存在",
                "resource_type": resource_type,
                "conflict_field": conflict_field,
                "conflict_value": conflict_value
            }
        )

class RateLimitExceededError(APIError):
    """速率限制超出错误"""
    def __init__(
        self,
        retry_after: int,
        limit: int,
        window: int
    ) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "请求过于频繁，请稍后再试",
                "retry_after": retry_after,
                "limit": limit,
                "window": window
            },
            headers={"Retry-After": str(retry_after)}
        )

class RateLimitError(RateLimitExceededError):
    """速率限制错误，是RateLimitExceededError的别名，提供兼容性"""
    def __init__(
        self,
        retry_after: int = 60,
        limit: int = 100,
        window: int = 3600
    ) -> None:
        super().__init__(retry_after, limit, window)

class ServiceUnavailableError(APIError):
    """服务不可用错误"""
    def __init__(
        self,
        service: str,
        detail: str = "服务暂时不可用"
    ) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": detail,
                "service": service
            }
        )

class DatabaseError(APIError):
    """
    数据库错误
    
    当数据库操作失败时抛出此异常。
    例如：连接失败、查询超时等。
    
    Attributes:
        detail: 错误详细信息，默认为"数据库操作失败"
        status_code: HTTP 500 INTERNAL SERVER ERROR
    """
    def __init__(
        self,
        operation: str,
        detail: str = "数据库操作失败"
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": detail,
                "operation": operation
            }
        )

class CacheError(APIError):
    """缓存错误"""
    def __init__(
        self,
        operation: str,
        detail: str = "缓存操作失败"
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": detail,
                "operation": operation
            }
        )

class BusinessLogicError(APIError):
    """业务逻辑错误"""
    def __init__(
        self,
        detail: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "message": detail,
                "error_code": error_code
            }
        )

class RequestDataError(APIError):
    """
    请求数据错误
    
    当请求数据不符合业务规则时抛出此异常。
    例如：数据格式错误、参数缺失等。
    
    Attributes:
        detail: 错误详细信息，默认为"请求数据无效"
        status_code: HTTP 400 BAD REQUEST
    """
    def __init__(
        self,
        detail: str = "请求数据无效",
        field_errors: Optional[Dict[str, str]] = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": detail,
                "field_errors": field_errors
            } if field_errors else detail
        )

class CaptchaError(APIError):
    """
    验证码错误
    
    当验证码验证失败时抛出此异常。
    例如：验证码错误、验证码过期等。
    
    Attributes:
        detail: 错误详细信息，默认为"验证码错误或已过期"
        status_code: HTTP 400 BAD REQUEST
    """
    def __init__(self, detail: str = "验证码错误或已过期") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class SQLAlchemyError(APIError):
    """SQLAlchemy数据库操作错误"""
    def __init__(
        self,
        detail: str = "数据库操作失败",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail=detail
        )

class NoResultFound(APIError):
    """查询无结果错误
    
    当在数据库中查询不到预期结果时抛出此异常。
    
    Attributes:
        detail: 错误详细信息，默认为"未找到查询结果"
        status_code: HTTP 404 NOT FOUND
    """
    def __init__(
        self,
        detail: str = "未找到查询结果",
        entity_name: Optional[str] = None
    ) -> None:
        message = detail
        if entity_name:
            message = f"{entity_name}: {detail}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )

class UserNotFoundError(APIError):
    """
    用户不存在错误
    
    当请求的用户不存在时抛出此异常。
    
    Attributes:
        user_id: 用户ID或用户名
        detail: 错误详细信息
        status_code: HTTP 404 NOT FOUND
    """
    def __init__(
        self,
        user_id: Any,
        detail: str = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": detail or f"用户 {user_id} 不存在",
                "code": "user_not_found",
                "user_id": user_id
            }
        )

"""
业务异常模块

提供统一的业务异常处理，使错误处理更加结构化和一致。
"""

class BusinessErrorCode(str, Enum):
    """业务错误码枚举"""
    # 通用错误码
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 内部错误
    VALIDATION_ERROR = "VALIDATION_ERROR"  # 验证错误
    NOT_FOUND = "NOT_FOUND"  # 资源不存在
    UNAUTHORIZED = "UNAUTHORIZED"  # 未授权
    FORBIDDEN = "FORBIDDEN"  # 禁止访问
    
    # 认证相关错误码
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"  # 无效的凭证
    TOKEN_EXPIRED = "TOKEN_EXPIRED"  # 令牌过期
    TOKEN_INVALID = "TOKEN_INVALID"  # 无效的令牌
    
    # 用户相关错误码
    USER_NOT_FOUND = "USER_NOT_FOUND"  # 用户不存在
    USER_INACTIVE = "USER_INACTIVE"  # 用户未激活
    USERNAME_TAKEN = "USERNAME_TAKEN"  # 用户名已被占用
    EMAIL_TAKEN = "EMAIL_TAKEN"  # 邮箱已被占用
    
    # 帖子相关错误码
    POST_NOT_FOUND = "POST_NOT_FOUND"  # 帖子不存在
    POST_DELETED = "POST_DELETED"  # 帖子已删除
    CREATE_ERROR = "CREATE_ERROR"  # 创建错误
    UPDATE_ERROR = "UPDATE_ERROR"  # 更新错误
    DELETE_ERROR = "DELETE_ERROR"  # 删除错误
    
    # 评论相关错误码
    COMMENT_NOT_FOUND = "COMMENT_NOT_FOUND"  # 评论不存在
    
    # 标签相关错误码
    TAG_NOT_FOUND = "TAG_NOT_FOUND"  # 标签不存在
    
    # 分类相关错误码
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"  # 分类不存在
    
    # 版块相关错误码
    SECTION_NOT_FOUND = "SECTION_NOT_FOUND"  # 版块不存在
    
    # 数据库相关错误码
    DB_ERROR = "DB_ERROR"  # 数据库错误

class BusinessException(Exception):
    """业务异常基类"""
    
    def __init__(
        self, 
        message: str = "业务处理异常", 
        code: Optional[str] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        """初始化业务异常
        
        Args:
            message: 异常信息
            code: 业务错误码，默认为None
            status_code: HTTP状态码，默认为400
            details: 详细错误信息，默认为None
        """
        self.message = message
        self.code = code if code else "BUSINESS_ERROR"
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

# 为了兼容性，添加BusinessError作为BusinessException的别名
BusinessError = BusinessException
