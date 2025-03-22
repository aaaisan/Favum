from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserSchema(BaseModel):
    """用户基础输入模型"""
    username: str
    email: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserSchema):
    """用户创建输入模型"""
    password: str
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码长度至少为8个字符')
        return v

# class UserUpdate(BaseModel):
#     """用户更新输入模型"""
#     username: Optional[str] = None
#     email: Optional[EmailStr] = None
#     bio: Optional[str] = None
#     avatar_url: Optional[str] = None
#     password: Optional[str] = None
    
#     @field_validator('password')
#     @classmethod
#     def password_strength(cls, v: Optional[str]) -> Optional[str]:
#         if v is not None and len(v) < 8:
#             raise ValueError('密码长度至少为8个字符')
#         return v 