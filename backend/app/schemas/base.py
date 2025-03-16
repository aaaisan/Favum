from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

T = TypeVar('T')

class BaseSchema(BaseModel):
    """基础模型，包含所有模型共有的字段"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DeleteResponse(BaseModel):
    """通用删除响应模型"""
    id: int
    message: str
    
    model_config = ConfigDict(from_attributes=True) 