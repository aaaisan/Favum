from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse

class UserInfoResponse(BaseSchema):
    """用户信息响应模型（简化版）"""
    username: str
    email: str
    role: str = "user"
    avatar: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserInfoResponse):
    """用户响应模型"""
    post_count: int = 0
    comment_count: int = 0
    vote_count: int = 0
    favorite_count: int = 0
    hashed_password: str
    
    model_config = ConfigDict(from_attributes=True)

class UserProfileResponse(UserResponse):
    """用户资料响应模型"""
    bio: Optional[str] = None
    # location: Optional[str] = None
    # website: Optional[str] = None
    joined_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserDeleteResponse(DeleteResponse):
    """用户删除响应模型"""
    message: str = "用户已成功删除"
    
    model_config = ConfigDict(from_attributes=True)

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore") 