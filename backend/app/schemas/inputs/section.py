from pydantic import BaseModel, Field
from typing import Optional

class SectionBase(BaseModel):
    """版块基础输入模型"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class SectionCreate(SectionBase):
    """版块创建输入模型"""
    pass

class SectionUpdate(BaseModel):
    """版块更新输入模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200) 