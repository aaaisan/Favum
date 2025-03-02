from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础用户模型
class UserBase(BaseModel):
    username: str
    email: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

# 用于创建用户时的模型
class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少为8个字符')
        return v

# 用于更新用户时的模型
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('密码长度至少为8个字符')
        return v

# 数据库返回的用户模型
class User(UserBase):
    id: int
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# 用户个人资料模型
class UserProfile(User):
    post_count: int
    comment_count: int
    last_login: Optional[datetime] = None
    join_date: datetime
    reputation: int = 0
    badges: List[str] = []
    
    class Config:
        orm_mode = True

# 仅用于API响应的简化用户信息模型
class UserInfo(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    role: str
    
    class Config:
        orm_mode = True

# 用户令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenPayload(BaseModel):
    sub: str
    exp: int
    role: str
    
# 用户删除模型（响应）
class UserDelete(BaseModel):
    id: int
    message: str = "用户已成功删除" 