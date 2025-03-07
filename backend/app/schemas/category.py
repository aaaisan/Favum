from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = None

class Category(CategoryBase):
    id: int
    created_at: datetime
    children: List['Category'] = []

    class Config:
        from_attributes = True

# 解决循环引用
Category.model_rebuild() 