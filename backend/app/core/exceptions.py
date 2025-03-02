from fastapi import HTTPException, status
from typing import Any, Optional, Dict

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

"""
业务异常模块

提供统一的业务异常处理，使错误处理更加结构化和一致。
"""

class BusinessError(Exception):
    """业务逻辑异常基类
    
    提供统一的业务异常接口，支持错误码、消息和HTTP状态码。
    所有业务相关异常应继承此类。
    """
    
    def __init__(
        self, 
        code: str, 
        message: str, 
        status_code: int = 400, 
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化业务异常
        
        Args:
            code: 错误代码，用于客户端识别错误类型
            message: 用户友好的错误消息
            status_code: HTTP状态码
            details: 错误的详细信息（可选）
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            错误的字典表示
        """
        error_dict = {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        return error_dict


class ResourceNotFoundError(BusinessError):
    """资源不存在异常"""
    
    def __init__(
        self, 
        resource_type: str, 
        resource_id: Any, 
        message: Optional[str] = None
    ):
        """初始化资源不存在异常
        
        Args:
            resource_type: 资源类型（如 'post', 'user', 'comment'）
            resource_id: 资源ID
            message: 自定义错误消息（可选）
        """
        super().__init__(
            code="resource_not_found",
            message=message or f"{resource_type}不存在: {resource_id}",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class PermissionDeniedError(BusinessError):
    """权限不足异常"""
    
    def __init__(
        self, 
        required_permission: Optional[str] = None, 
        message: Optional[str] = None
    ):
        """初始化权限不足异常
        
        Args:
            required_permission: 所需权限（可选）
            message: 自定义错误消息（可选）
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
            
        super().__init__(
            code="permission_denied",
            message=message or "权限不足，无法执行此操作",
            status_code=403,
            details=details
        )


class ValidationError(BusinessError):
    """数据验证异常"""
    
    def __init__(
        self, 
        field: Optional[str] = None, 
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化数据验证异常
        
        Args:
            field: 验证失败的字段名（可选）
            message: 自定义错误消息（可选）
            details: 详细错误信息（可选）
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(
            code="validation_error",
            message=message or "数据验证失败",
            status_code=422,
            details=error_details
        )


class RateLimitError(BusinessError):
    """请求频率限制异常"""
    
    def __init__(
        self, 
        limit: Optional[int] = None, 
        reset_seconds: Optional[int] = None, 
        message: Optional[str] = None
    ):
        """初始化请求频率限制异常
        
        Args:
            limit: 允许的请求次数（可选）
            reset_seconds: 重置时间（秒）（可选）
            message: 自定义错误消息（可选）
        """
        details = {}
        if limit is not None:
            details["limit"] = limit
        if reset_seconds is not None:
            details["reset_seconds"] = reset_seconds
            
        super().__init__(
            code="rate_limit_exceeded",
            message=message or "请求频率超出限制，请稍后再试",
            status_code=429,
            details=details
        )


class AuthenticationError(BusinessError):
    """认证异常"""
    
    def __init__(self, message: Optional[str] = None):
        """初始化认证异常
        
        Args:
            message: 自定义错误消息（可选）
        """
        super().__init__(
            code="authentication_error",
            message=message or "认证失败，请重新登录",
            status_code=401
        )


class ServiceUnavailableError(BusinessError):
    """服务不可用异常"""
    
    def __init__(self, service: Optional[str] = None, message: Optional[str] = None):
        """初始化服务不可用异常
        
        Args:
            service: 不可用的服务名称（可选）
            message: 自定义错误消息（可选）
        """
        details = {}
        if service:
            details["service"] = service
            
        super().__init__(
            code="service_unavailable",
            message=message or "服务暂时不可用，请稍后再试",
            status_code=503,
            details=details
        ) 