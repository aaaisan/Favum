from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserResponse(BaseModel):
    """用户响应模型
    
    用于API返回用户对象的标准格式
    """
    id: int
    username: str
    email: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    """用户个人资料响应模型
    
    包含扩展的用户信息，用于个人资料页面
    """
    post_count: int
    comment_count: int
    last_login: Optional[datetime] = None
    join_date: datetime
    reputation: int = 0
    badges: List[str] = []
    
    class Config:
        from_attributes = True

class UserInfoResponse(BaseModel):
    """简化的用户信息响应模型
    
    适用于列表和引用场景
    """
    id: int
    username: str
    avatar_url: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    
    class Config:
        from_attributes = True

class UserDeleteResponse(BaseModel):
    """用户删除响应模型"""
    id: int
    message: str = "用户已成功删除" 