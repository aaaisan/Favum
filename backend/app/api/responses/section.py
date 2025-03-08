from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class SectionResponse(BaseModel):
    """板块响应模型
    
    用于API返回板块对象的标准格式
    """
    id: int
    name: str
    description: str
    created_at: datetime
    post_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class SectionDetailResponse(SectionResponse):
    """板块详情响应模型
    
    包含更多详细信息的板块响应模型
    """
    category_count: Optional[int] = 0
    last_post_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SectionListResponse(BaseModel):
    """板块列表响应模型"""
    sections: List[SectionResponse]
    total: int
    
    class Config:
        from_attributes = True 