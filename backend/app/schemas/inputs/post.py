from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class VoteType(str, Enum):
    """点赞类型枚举"""
    UPVOTE = "upvote"    # 点赞
    DOWNVOTE = "downvote"  # 反对

class PostBase(BaseModel):
    """帖子基础输入模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    section_id: Optional[int] = None
    tags: Optional[List[str]] = []

class PostCreate(PostBase):
    """帖子创建输入模型"""
    pass

class PostUpdate(BaseModel):
    """帖子更新输入模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    section_id: Optional[int] = None
    tags: Optional[List[str]] = None

class PostVoteCreate(BaseModel):
    """帖子投票创建输入模型"""
    vote_type: VoteType

class PostFavoriteCreate(BaseModel):
    """帖子收藏创建输入模型"""
    # 不需要任何字段，post_id从URL路径获取，user_id从当前用户获取
    pass 