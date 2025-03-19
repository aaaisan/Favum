from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse
from .user import UserInfoResponse
from .comment import CommentResponse
from .tag import TagResponse
from .section import SectionResponse
from .category import CategoryResponse

class PostResponse(BaseSchema):
    """帖子响应模型"""
    title: str
    content: str
    author_id: int
    category_id: Optional[int] = None
    section_id: Optional[int] = None
    view_count: int = 0
    comment_count: int = 0
    vote_count: int = 0
    upvote_count: int = 0
    downvote_count: int = 0
    author: Optional[UserInfoResponse] = None
    category: Optional[CategoryResponse] = None
    section: Optional[SectionResponse] = None
    tags: List[TagResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class PostDetailResponse(PostResponse):
    """帖子详细响应模型"""
    user_vote: Optional[str] = None  # "upvote" or "downvote" or None
    is_favorited: bool = False
    is_author: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class PostDeleteResponse(DeleteResponse):
    """帖子删除响应模型"""
    message: str = "帖子已成功删除"
    post_id: int
    
    model_config = ConfigDict(from_attributes=True)

class PostListResponse(BaseModel):
    """帖子列表响应模型"""
    posts: List[PostResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")

class PostStatsResponse(BaseSchema):
    """帖子统计响应模型"""
    post_id: int
    vote_count: int = 0
    comment_count: int = 0
    view_count: int = 0
    upvote_count: int = 0
    downvote_count: int = 0
    favorite_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class PostVoteResponse(BaseSchema):
    """帖子投票响应模型"""
    post_id: int
    upvotes: int
    downvotes: int
    score: int
    user_vote: Optional[str] = None  # "upvote" or "downvote" or None
    action: str  # "voted" or "unvoted"
    
    model_config = ConfigDict(from_attributes=True)

class PostFavoriteResponse(BaseSchema):
    """帖子收藏响应模型"""
    post_id: int
    user_id: int
    status: str  # "favorited" or "unfavorited" or "already_favorited"
    favorite_id: Optional[int] = None
    created_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PostCommentResponse(BaseSchema):
    """帖子评论列表响应模型"""
    post_id: int
    comments: List[CommentResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True) 