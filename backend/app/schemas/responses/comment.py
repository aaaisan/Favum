from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse
from .user import UserInfoResponse

class CommentResponse(BaseSchema):
    """评论响应模型"""
    content: str
    post_id: int
    author_id: int
    parent_id: Optional[int] = None
    reply_count: int = 0
    author: Optional[UserInfoResponse] = None
    replies: List['CommentResponse'] = []
        
    model_config = ConfigDict(from_attributes=True)

class CommentDetailResponse(CommentResponse):
    """评论详细响应模型"""
    is_author: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class CommentDeleteResponse(DeleteResponse):
    """评论删除响应模型"""
    message: str = "评论已成功删除"
    
    model_config = ConfigDict(from_attributes=True)

class CommentListResponse(BaseModel):
    """评论列表响应模型"""
    comments: List[CommentResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")

# 更新 CommentResponse 的 Forward Reference
CommentResponse.model_rebuild() 