from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from enum import Enum

# Import your schema definitions
# from ...schemas.post import Post, PublicPost  # 导入现有的Post模式

# 引入其他响应模型，用于关联对象
from .user import UserInfoResponse
from .tag import TagResponse
from .category import CategoryResponse
from .section import SectionResponse
from .comment import CommentListResponse

# # 添加缺少的SectionResponse定义
# class SectionResponse(BaseModel):
#     """版块响应"""
#     id: int
#     name: str
    
#     model_config = {"extra": "ignore"}

# 添加点赞类型枚举 - 与schemas保持一致
class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

# 基础帖子模型
class PostBase(BaseModel):
    title: str
    content: str
    category_id: int
    
    model_config = ConfigDict(from_attributes=True)

# 创建帖子请求模型
class PostCreate(PostBase):
    author_id: int
    section_id: int
    tag_ids: Optional[List[int]] = None
    
    model_config = ConfigDict(from_attributes=True)

# 更新帖子请求模型
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    is_hidden: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)

# 标准帖子响应模型
class PostResponse(BaseModel):
    """帖子响应"""
    id: int
    title: str
    content: str
    author_id: int
    section_id: Optional[int] = None
    category_id: Optional[int] = None
    is_hidden: bool = False
    created_at: str  # 使用字符串类型接收ISO格式的日期时间
    updated_at: Optional[str] = None
    is_deleted: bool = False
    vote_count: int = 0
    category: Optional[dict] = None  # 保留完整结构但使用dict类型
    section: Optional[dict] = None   # 保留完整结构但使用dict类型
    tags: Optional[List[dict]] = None  # 保留完整结构但使用dict类型
    author: Optional[dict] = None    # 保留完整结构但使用dict类型
    tag_ids: Optional[List[int]] = None  # 添加tag_ids字段，用于ID引用模式
    
    model_config = ConfigDict(extra="ignore")

# 公开帖子信息，仅包含非敏感内容
class PublicPostResponse(BaseModel):
    id: int
    title: str
    content: str
    is_hidden: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    vote_count: Optional[int] = 0
    category_id: int
    
    model_config = ConfigDict(from_attributes=True)

# 帖子详情响应模型
class PostDetailResponse(BaseModel):
    """帖子详情响应"""
    id: int
    title: str
    content: str
    author_id: int
    section_id: Optional[int] = None
    category_id: Optional[int] = None
    is_hidden: bool = False
    created_at: str  # 使用字符串类型接收ISO格式的日期时间
    updated_at: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[str] = None  # 添加这个字段，因为实际数据中可能存在
    vote_count: int = 0
    view_count: Optional[int] = 0
    favorite_count: Optional[int] = 0
    category: Optional[dict] = None  # 保留完整结构但使用dict类型
    section: Optional[dict] = None   # 保留完整结构但使用dict类型
    tags: Optional[List[dict]] = None  # 保留完整结构但使用dict类型
    author: Optional[dict] = None    # 保留完整结构但使用dict类型
    comments: Optional[List] = None  # 使用List类型以适应任意结构的评论
    tag_ids: Optional[List[int]] = None  # 添加tag_ids字段，用于ID引用模式
    
    model_config = ConfigDict(extra="ignore")

# 帖子列表响应模型
class PostListResponse(BaseModel):
    """帖子列表响应"""
    posts: List[dict]  # 使用dict
    total: int
    page: Optional[int] = 1
    size: Optional[int] = 10
    
    model_config = ConfigDict(extra="ignore")

# 帖子评论响应模型
class PostCommentResponse(BaseModel):
    """帖子评论列表响应"""
    post_id: int
    comments: List
    total: int
    page: int
    size: int
    
    model_config = {"extra": "ignore"}

# 帖子统计响应模型
class PostStatsResponse(BaseModel):
    """帖子统计响应"""
    post_id: int
    vote_count: int
    
    model_config = {"extra": "ignore"}

# 帖子删除响应模型
class PostDeleteResponse(BaseModel):
    """帖子删除响应"""
    message: str
    post_id: int
    
    model_config = {"extra": "ignore"}

# 帖子投票创建请求模型
class PostVoteCreate(BaseModel):
    vote_type: VoteType
    
    model_config = ConfigDict(from_attributes=True)

# 帖子投票记录模型
class PostVote(BaseModel):
    id: int
    post_id: int
    user_id: int
    vote_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 帖子投票响应模型 - 保留特定字段以兼容现有代码
class PostVoteResponse(BaseModel):
    """帖子投票响应"""
    post_id: int
    upvotes: int
    downvotes: int
    score: int
    user_vote: Optional[str] = None
    action: str
    
    model_config = {"extra": "ignore"}

# 点赞响应模型 - 与schema保持一致
class VoteResponse(BaseModel):
    success: bool
    vote_count: int
    message: str
    
    model_config = ConfigDict(from_attributes=True)

# 收藏帖子请求模型
class PostFavoriteCreate(BaseModel):
    pass  # 不需要任何字段，post_id从URL路径获取，user_id从当前用户获取
    
    model_config = ConfigDict(from_attributes=True)

# 帖子收藏记录模型
class PostFavorite(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 帖子收藏响应模型
class PostFavoriteResponse(BaseModel):
    """帖子收藏响应"""
    post_id: int
    user_id: int
    status: str
    favorite_id: Optional[int] = None
    created_at: Optional[str] = None
    
    model_config = {"extra": "ignore"}

# 收藏操作响应模型
class FavoriteResponse(BaseModel):
    success: bool
    message: str
    
    model_config = ConfigDict(from_attributes=True)

# 用户收藏列表模型
class PostFavoritesList(BaseModel):
    posts: List[PostResponse]
    total: int
    
    model_config = ConfigDict(from_attributes=True)

# 使用同样的方式修改或新增其他响应类... 