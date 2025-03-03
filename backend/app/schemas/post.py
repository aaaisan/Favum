from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .tag import Tag
from .category import Category
from enum import Enum

# 添加点赞类型枚举
class VoteType(str, Enum):
    UPVOTE = "upvote"    # 点赞
    DOWNVOTE = "downvote"  # 反对

class PostBase(BaseModel):
    title: str
    content: str
    category_id: int

class PostCreate(PostBase):
    author_id: int
    section_id: int
    tag_ids: Optional[List[int]] = None

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    is_hidden: Optional[bool] = None

class Post(PostBase):
    id: int
    author_id: int
    section_id: int
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime
    vote_count: Optional[int] = 0  # 修改为可选字段
    category: Optional[Category] = None
    tags: List[Tag] = []

    class Config:
        from_attributes = True

class PublicPost(BaseModel):
    """公开帖子信息，仅包含非敏感内容
    
    用于游客查看，不需要登录
    """
    id: int
    title: str
    content: str
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime
    vote_count: Optional[int] = 0  # 修改为可选字段
    category: Optional[Category] = None
    
    class Config:
        from_attributes = True

# 添加点赞请求模型
class PostVoteCreate(BaseModel):
    vote_type: VoteType

# 添加点赞响应模型
class PostVote(BaseModel):
    id: int
    post_id: int
    user_id: int
    vote_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 点赞响应模型
class VoteResponse(BaseModel):
    success: bool
    vote_count: int
    message: str

# 添加收藏相关模型
class PostFavoriteCreate(BaseModel):
    """收藏帖子请求模型，不需要任何字段，
    因为post_id将从URL路径获取，user_id将从当前用户获取"""
    pass

class PostFavorite(BaseModel):
    """收藏记录模型"""
    id: int
    post_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FavoriteResponse(BaseModel):
    """收藏操作响应模型"""
    success: bool
    message: str

class PostFavoritesList(BaseModel):
    """用户收藏列表模型"""
    posts: List[Post]
    total: int

class PostList(BaseModel):
    """帖子列表响应模型"""
    posts: List[Post]
    total: int
    page_size: int
    
    class Config:
        from_attributes = True 