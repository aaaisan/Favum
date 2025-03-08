from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class Login(BaseModel):
    username: str
    password: str
    captcha_id: str  # 验证码ID，必填
    captcha_code: str  # 验证码，必填

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    captcha_id: str
    captcha_code: str 

class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(..., description="用户注册的邮箱")
    
class PasswordReset(BaseModel):
    """密码重置模型"""
    token: str = Field(..., description="密码重置令牌")
    new_password: str = Field(..., min_length=6, description="新密码，至少6个字符")
    
class EmailVerification(BaseModel):
    """邮箱验证模型"""
    email: EmailStr = Field(..., description="要验证的邮箱地址")
    token: str = Field(..., description="邮箱验证令牌") 