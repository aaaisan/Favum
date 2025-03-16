from pydantic import BaseModel, Field
from typing import Optional

class TagBase(BaseModel):
    """标签基础输入模型"""
    name: str = Field(..., min_length=1, max_length=30)

class TagCreate(TagBase):
    """标签创建输入模型"""
    pass

class TagUpdate(BaseModel):
    """标签更新输入模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=30) 