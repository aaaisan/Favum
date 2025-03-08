from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class CategoryResponse(BaseModel):
    """类别响应模型
    
    用于API返回类别对象的标准格式
    """
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    order: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoryDetailResponse(CategoryResponse):
    """类别详情响应模型，包含子类别
    
    用于返回完整的类别层次结构
    """
    children: List['CategoryDetailResponse'] = []
    
    class Config:
        from_attributes = True

# 解决循环引用
CategoryDetailResponse.model_rebuild()

class CategoryListResponse(BaseModel):
    """类别列表响应模型"""
    categories: List[CategoryResponse]
    total: int
    
    class Config:
        from_attributes = True

class CategoryTreeResponse(BaseModel):
    """类别树响应模型
    
    用于返回完整的类别层次结构树
    """
    categories: List[CategoryDetailResponse]
    
    class Config:
        from_attributes = True 