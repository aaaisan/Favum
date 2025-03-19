from pydantic import BaseModel, Field
from typing import Optional, List
from .post import PostBase
from .user import UserBase

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

class SectionDelete(BaseModel):
    """版块删除输入模型"""
    message: Optional[str] = 'deleted'

class SectionRestore(BaseModel):
    """版块恢复输入模型"""
    message: Optional[str] = 'restored'

class SectionModeratorAdd(BaseModel):
    """添加版主输入模型"""
    section_id: int
    user_id: int
    message: Optional[str] = 'moderator added'

class SectionModeratorRemove(BaseModel):
    """移除版主输入模型"""
    section_id: int
    user_id: int
    message: Optional[str] = 'moderator removed'

class SectionModeratorRestore(BaseModel):
    """恢复版主输入模型"""
    section_id: int
    user_id: int
    message: Optional[str] = 'moderator restored'

