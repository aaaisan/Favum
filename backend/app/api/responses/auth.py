from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from datetime import datetime

class TokenResponse(BaseModel):
    """用户令牌响应模型
    
    用于API返回访问令牌的标准格式
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 令牌过期时间（秒）
    
    class Config:
        from_attributes = True

class TokenDataResponse(BaseModel):
    """令牌数据响应模型
    
    用于API验证令牌的响应
    """
    username: Optional[str] = None
    user_id: int
    role: str
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

class LoginCheckResponse(BaseModel):
    """登录检查响应模型
    
    用于检查用户名/邮箱是否存在的响应
    """
    exists: bool
    message: str
    
    class Config:
        from_attributes = True

class AuthErrorResponse(BaseModel):
    """认证错误响应模型"""
    detail: str
    error_code: Optional[str] = None
    
    class Config:
        from_attributes = True