from pydantic import BaseModel, Field
from typing import Optional

class CommentSchema(BaseModel):
    """评论基础输入模型"""
    content: str = Field(..., min_length=1)
    post_id: int
    parent_id: Optional[int] = None


# class CommentUpdate(BaseModel):
#     """评论更新输入模型"""
#     content: Optional[str] = Field(None, min_length=1) 