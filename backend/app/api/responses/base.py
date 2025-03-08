from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar('T')

class BaseResponse(BaseModel):
    """基本响应模型
    
    所有API响应的基础模型
    """
    success: bool = True
    message: Optional[str] = None
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error_code: Optional[str] = None
    detail: Optional[str] = None
    
    class Config:
        from_attributes = True

class DataResponse(GenericModel, Generic[T]):
    """带数据的响应模型
    
    用于包装任何类型的数据响应
    """
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    
    class Config:
        from_attributes = True

class PaginatedResponse(GenericModel, Generic[T]):
    """分页响应模型
    
    适用于所有分页列表数据
    """
    success: bool = True
    message: Optional[str] = None
    data: List[T] = []
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True 