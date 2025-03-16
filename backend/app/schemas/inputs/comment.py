from pydantic import BaseModel, Field
from typing import Optional

class CommentBase(BaseModel):
    """评论基础输入模型"""
    content: str = Field(..., min_length=1)
    post_id: int
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    """评论创建输入模型"""
    pass

class CommentUpdate(BaseModel):
    """评论更新输入模型"""
    content: Optional[str] = Field(None, min_length=1) 