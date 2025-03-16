from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse

class CategoryResponse(BaseSchema):
    """分类响应模型"""
    name: str
    description: Optional[str] = None
    post_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class CategoryDetailResponse(CategoryResponse):
    """分类详细响应模型"""
    children: List['CategoryDetailResponse'] = []
    
    model_config = ConfigDict(from_attributes=True)

class CategoryDeleteResponse(DeleteResponse):
    """分类删除响应模型"""
    message: str = "分类已成功删除"
    
    model_config = ConfigDict(from_attributes=True)

class CategoryListResponse(BaseModel):
    """分类列表响应模型"""
    categories: List[CategoryResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")

class CategoryTreeResponse(BaseModel):
    """分类树响应模型"""
    categories: List[CategoryDetailResponse]
    
    model_config = ConfigDict(from_attributes=True)

# 更新 CategoryDetailResponse 的 Forward Reference
CategoryDetailResponse.model_rebuild() 