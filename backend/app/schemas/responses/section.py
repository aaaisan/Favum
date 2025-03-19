from typing import Optional, List, Dict, Any
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

# 以下是缺失的响应模型

class SectionCreateResponse(SectionDetailResponse):
    """版块创建响应模型"""
    message: str = "版块创建成功"
    
    model_config = ConfigDict(from_attributes=True)

class SectionUpdateResponse(SectionDetailResponse):
    """版块更新响应模型"""
    message: str = "版块更新成功"
    
    model_config = ConfigDict(from_attributes=True)

class SectionRestoreResponse(SectionDetailResponse):
    """版块恢复响应模型"""
    message: str = "版块恢复成功"
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorAddResponse(BaseModel):
    """添加版主响应模型"""
    message: str
    section_id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorRemoveResponse(BaseModel):
    """移除版主响应模型"""
    message: str
    section_id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorRestoreResponse(BaseModel):
    """恢复版主响应模型"""
    message: str
    section_id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)

class SectionPostListResponse(BaseModel):
    """版块帖子列表响应模型"""
    posts: List[Dict[str, Any]]
    total: int
    page: int = 1
    size: int = 20
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorItem(BaseModel):
    """版主信息项"""
    user_id: int
    username: str
    avatar: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorList(BaseModel):
    """版主列表响应模型"""
    moderators: List[SectionModeratorItem]
    total: int
    
    model_config = ConfigDict(from_attributes=True)

class SectionModeratorListResponse(BaseModel):
    """版主列表响应模型包装"""
    data: SectionModeratorList
    section_id: int
    
    model_config = ConfigDict(from_attributes=True)