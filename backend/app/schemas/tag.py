from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None

class Tag(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TagRecommendationRequest(BaseModel):
    """标签推荐请求模型"""
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    user_id: Optional[int] = Field(None, description="用户ID，用于基于用户历史的推荐") 