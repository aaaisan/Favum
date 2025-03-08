from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Import your schema definitions
# from ...schemas.post import Post, PublicPost  # 导入现有的Post模式

# 引入其他响应模型，用于关联对象
from .user import UserInfoResponse
from .tag import TagResponse
from .category import CategoryResponse
from .comment import CommentResponse

# 确保嵌套对象包含所有必要字段
# class TagResponse(BaseModel):
#     id: int
#     name: str
#     created_at: datetime  # 添加创建时间字段

# class CategoryResponse(BaseModel):
#     id: int
#     name: str
#     created_at: datetime  # 添加创建时间字段

# 修改帖子响应，确保嵌套对象使用上面定义的响应模型
class PostResponse(BaseModel):
    """帖子响应模型
    
    用于API返回帖子对象的标准格式
    """
    id: int
    title: str
    content: str
    author_id: int
    category_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    vote_count: int = 0
    comment_count: int = 0
    is_published: bool = True
    is_pinned: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class PostDetailResponse(PostResponse):
    """帖子详情响应模型
    
    包含完整的帖子信息，包括作者、类别和标签
    """
    author: UserInfoResponse
    category: CategoryResponse
    tags: List[TagResponse] = []
    view_count: int = 0
    favorite_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class PostListResponse(BaseModel):
    """帖子列表响应模型
    
    用于返回分页的帖子列表
    """
    posts: List[PostDetailResponse]
    total: int
    page: int = 1
    size: int = 20
    
    model_config = ConfigDict(from_attributes=True)

class PostCommentResponse(BaseModel):
    """帖子评论响应模型
    
    用于返回帖子的评论列表
    """
    post_id: int
    comments: List[CommentResponse]
    total: int
    page: int = 1
    size: int = 20
    
    model_config = ConfigDict(from_attributes=True)

class PostStatsResponse(BaseModel):
    """帖子统计响应模型
    
    用于返回帖子的统计信息
    """
    post_id: int
    view_count: int = 0
    vote_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class PostDeleteResponse(BaseModel):
    """帖子删除响应模型"""
    id: int
    message: str = "帖子已成功删除"
    
class PostVoteResponse(BaseModel):
    """帖子投票响应模型"""
    post_id: int
    vote_value: int
    vote_count: int
    
    model_config = ConfigDict(from_attributes=True)

class PostFavoriteResponse(BaseModel):
    """帖子收藏响应模型"""
    post_id: int
    favorited: bool
    favorite_count: int
    
    model_config = ConfigDict(from_attributes=True)

# 使用同样的方式修改或新增其他响应类... 