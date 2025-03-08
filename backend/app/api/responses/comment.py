from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .user import UserInfoResponse

class CommentResponse(BaseModel):
    """评论响应模型
    
    用于API返回评论对象的标准格式
    """
    id: int
    content: str
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: Optional[bool] = False
    
    # 可选关联字段，根据实际需要返回
    author: Optional[UserInfoResponse] = None
    
    class Config:
        from_attributes = True

class CommentListResponse(BaseModel):
    """评论列表响应模型"""
    comments: List[CommentResponse]
    total: int
    post_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class CommentDeleteResponse(BaseModel):
    """评论删除响应模型"""
    id: int
    message: str = "评论已成功删除" 