from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class TagResponse(BaseModel):
    """标签响应模型
    
    用于API返回标签对象的标准格式
    """
    id: int
    name: str
    created_at: str  # 使用字符串类型接收ISO格式的日期时间
    post_count: Optional[int] = 0
    
    model_config = {"extra": "ignore"}

class TagListResponse(BaseModel):
    """标签列表响应模型"""
    tags: List[TagResponse]
    total: int
    
    class Config:
        from_attributes = True

class TagWithPostsResponse(TagResponse):
    """包含帖子数量的标签响应模型
    
    用于标签云和热门标签展示
    """
    post_count: int
    
    class Config:
        from_attributes = True

class TagCloudResponse(BaseModel):
    """标签云响应模型"""
    tags: List[TagWithPostsResponse]
    
    class Config:
        from_attributes = True 