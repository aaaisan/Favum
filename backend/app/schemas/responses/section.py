from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse

class SectionResponse(BaseSchema):
    """版块响应模型"""
    name: str
    description: Optional[str] = None
    post_count: int = 0
    last_post_time: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SectionDetailResponse(SectionResponse):
    """版块详细响应模型"""
    pass
    
    model_config = ConfigDict(from_attributes=True)

class SectionStatsResponse(SectionResponse):
    pass

class SectionDeleteResponse(DeleteResponse):
    """版块删除响应模型"""
    message: str = "版块已成功删除"
    
    model_config = ConfigDict(from_attributes=True)

class SectionListResponse(BaseModel):
    """版块列表响应模型"""
    sections: List[SectionResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore") 