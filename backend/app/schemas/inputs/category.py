from pydantic import BaseModel, Field
from typing import Optional, List

class CategorySchema(BaseModel):
    """分类基础输入模型"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class CategoryReorder(BaseModel):
    """分类重新排序输入模型"""
    category_ids: List[int]
    parent_id: Optional[int] = None 