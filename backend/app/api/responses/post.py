from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Import your schema definitions
from ...schemas.post import Post, PublicPost  # 导入现有的Post模式

# 确保嵌套对象包含所有必要字段
class TagResponse(BaseModel):
    id: int
    name: str
    created_at: datetime  # 添加创建时间字段

class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime  # 添加创建时间字段

# 修改帖子响应，确保嵌套对象使用上面定义的响应模型
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    category_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    vote_count: int = 0
    category: CategoryResponse
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    
    class Config:
        from_attributes = True

# 使用同样的方式修改或新增其他响应类... 