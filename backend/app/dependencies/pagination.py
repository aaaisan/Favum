from fastapi import Query
from typing import Optional, Dict, Any
# from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SortOrder(str, Enum):
    """排序顺序枚举"""
    ASC = "asc"
    DESC = "desc"

async def get_pagination_params(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数，最大100"),
):
    """获取分页参数
    
    Args:
        page: 页码，从1开始
        page_size: 每页记录数，默认20，最大100
        
    Returns:
        Dict: 包含分页参数的字典
    """
    skip = (page - 1) * page_size
    return {
        "skip": skip,
        "limit": page_size,
        "page": page,
        "page_size": page_size
    }

async def get_sorting_params(
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="排序顺序")
):
    """获取排序参数
    
    Args:
        sort_by: 排序字段名称
        sort_order: 排序顺序，asc或desc
        
    Returns:
        Dict: 包含排序参数的字典
    """
    return {
        "sort_by": sort_by,
        "sort_order": sort_order
    }

async def get_post_filters(
    category_id: Optional[int] = Query(None, description="分类ID"),
    tag: Optional[str] = Query(None, description="标签"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_pinned: Optional[bool] = Query(None, description="是否置顶"),
    created_after: Optional[datetime] = Query(None, description="创建时间晚于"),
    created_before: Optional[datetime] = Query(None, description="创建时间早于"),
    author_id: Optional[int] = Query(None, description="作者ID")
):
    """获取帖子过滤条件
    
    Args:
        category_id: 分类ID
        tag: 标签
        search: 搜索关键词
        is_pinned: 是否置顶
        created_after: 创建时间晚于
        created_before: 创建时间早于
        author_id: 作者ID
        
    Returns:
        Dict: 包含过滤条件的字典
    """
    filters: Dict[str, Any] = {}
    
    if category_id:
        filters["category_id"] = category_id
    
    if tag:
        filters["tag"] = tag
    
    if search:
        filters["search"] = search
    
    if is_pinned is not None:
        filters["is_pinned"] = is_pinned
    
    if created_after:
        filters["created_after"] = created_after
    
    if created_before:
        filters["created_before"] = created_before
    
    if author_id:
        filters["author_id"] = author_id
    
    return filters 