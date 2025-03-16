from typing import Optional, List, Union, Dict
from datetime import datetime
from ..base import BaseSchema
from .user import UserInfoResponse

class TokenResponse(BaseSchema):
    """Token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfoResponse

class TokenDataResponse(BaseSchema):
    """令牌数据响应模型"""
    username: Optional[str] = None
    user_id: int
    role: str
    permissions: List[str] = []

class TokenVerifyResponse(BaseSchema):
    """Token验证响应模型"""
    valid: bool
    user: Dict[str, Union[int, str, bool]]

class LoginCheckResponse(BaseSchema):
    """登录检查响应模型"""
    exists: bool
    message: str

class TokenValidationResponse(BaseSchema):
    """Token验证响应模型"""
    is_valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None

class AuthErrorResponse(BaseSchema):
    """认证错误响应模型"""
    detail: str
    error_code: Optional[str] = None

class PasswordResetRequestResponse(BaseSchema):
    """密码重置请求响应模型"""
    message: str = "密码重置邮件已发送"
    email: str
    success: bool = True

class PasswordResetResponse(BaseSchema):
    """密码重置响应模型"""
    message: str = "密码重置成功"

class PasswordChangeResponse(BaseSchema):
    """密码修改响应模型"""
    message: str = "密码修改成功"

class EmailVerificationResponse(BaseSchema):
    """邮箱验证响应模型"""
    message: str

class EmailVerificationRedirectResponse(BaseSchema):
    """带重定向的邮箱验证响应模型"""
    message: str
    redirect: str 