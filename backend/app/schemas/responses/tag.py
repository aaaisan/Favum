from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from ..base import BaseSchema, DeleteResponse

class TagResponse(BaseSchema):
    """标签响应模型"""
    name: str
    post_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class TagDetailResponse(TagResponse):
    """标签详细响应模型"""
    pass
    
    model_config = ConfigDict(from_attributes=True)

class TagDeleteResponse(DeleteResponse):
    """标签删除响应模型"""
    message: str = "标签已成功删除"
    
    model_config = ConfigDict(from_attributes=True)

# 用于标签云和热门标签展示
class TagWithPostsResponse(TagResponse):
    """包含帖子数量的标签响应模型"""
    post_count: int
    
    model_config = ConfigDict(from_attributes=True)

class TagCloudResponse(BaseSchema):
    """标签云响应模型"""
    tags: List[TagWithPostsResponse]
    
    model_config = ConfigDict(from_attributes=True)

class TagFollowResponse(BaseModel):
    """标签关注响应模型"""
    tag_id: int
    user_id: int
    status: str  # "following", "unfollowed", "already_following"
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")

class TagListResponse(BaseModel):
    """标签列表响应模型"""
    tags: List[TagResponse]
    total: int
    page: int = 1
    size: int = 10
    
    model_config = ConfigDict(from_attributes=True, extra="ignore") 