from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class CaptchaInput(BaseModel):
    """验证码输入模型"""
    captcha_id: str  # 验证码ID
    captcha_code: str  # 验证码

class LoginInput(BaseModel):
    """登录输入模型"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class Login(LoginInput, CaptchaInput):
    """登录输入模型（包含验证码）"""
    pass
    
class UserRegister(LoginInput, CaptchaInput):
    """用户注册输入模型"""
    pass


class TokenRefreshInput(BaseModel):
    """Token刷新输入模型"""
    refresh_token: str

class PasswordResetRequestInput(BaseModel):
    """密码重置请求输入模型"""
    email: EmailStr

class PasswordResetInput(BaseModel):
    """密码重置输入模型"""
    token: str
    new_password: str = Field(..., min_length=6)

class PasswordChangeInput(BaseModel):
    """密码修改输入模型"""
    old_password: str
    new_password: str = Field(..., min_length=6)
    
class EmailVerificationInput(BaseModel):
    """邮箱验证输入模型"""
    email: EmailStr = Field(..., description="要验证的邮箱地址")
    token: str = Field(..., description="邮箱验证令牌") 