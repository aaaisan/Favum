from fastapi import APIRouter, HTTPException, Request, status
from typing import List, Optional

# 导入响应模型

from ..responses import (
    TagResponse,
    TagListResponse,
    TagWithPostsResponse,
    TagCloudResponse
)
from ..responses.post import PostListResponse

from ...schemas import tag as tag_schema
from ...schemas import post as post_schema
from ...services.tag_service import TagService
from ...core.exceptions import BusinessException
from ...core.decorators import public_endpoint, admin_endpoint

router = APIRouter()

@router.post("/", response_model=TagResponse)
@admin_endpoint(custom_message="创建标签失败")
async def create_tag(
    request: Request,
    tag: tag_schema.TagCreate
):
    """创建新标签
    
    创建一个新的帖子标签。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        tag: 标签创建模型，包含标签信息
        
    Returns:
        TagResponse: 创建成功的标签信息
        
    Raises:
        HTTPException: 当标签已存在时抛出400错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 创建标签
        result = await tag_service.create_tag(tag.model_dump())
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/", response_model=TagListResponse)
@public_endpoint(cache_ttl=300, custom_message="获取标签列表失败")
async def read_tags(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """获取所有标签列表
    
    返回所有可用的标签列表，支持分页。
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        TagListResponse: 标签列表及总数
        
    Raises:
        HTTPException: 当获取标签失败时抛出相应错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 获取标签列表
        tags, total = await tag_service.get_tags(skip=skip, limit=limit)
        
        # 构建符合TagListResponse的返回结构
        return {
            "tags": tags,
            "total": total
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/popular", response_model=TagCloudResponse)
@public_endpoint(cache_ttl=300, custom_message="获取热门标签失败")
async def read_popular_tags(
    request: Request,
    limit: int = 10
):
    """获取热门标签
    
    获取使用次数最多的标签列表。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        limit: 返回的标签数量，默认10
        
    Returns:
        TagCloudResponse: 热门标签列表，按使用次数降序排序
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 获取热门标签
        popular_tags = await tag_service.get_popular_tags(limit=limit)
        
        # 构建符合TagCloudResponse的返回结构
        return {
            "tags": popular_tags
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/recent", response_model=TagCloudResponse)
@public_endpoint(cache_ttl=300, custom_message="获取最近标签失败")
async def read_recent_tags(
    request: Request,
    limit: int = 10
):
    """获取最近标签
    
    获取最近使用的标签列表。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        limit: 返回的标签数量，默认10
        
    Returns:
        TagCloudResponse: 最近使用的标签列表，按最后使用时间降序排序
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 获取最近标签
        recent_tags = await tag_service.get_recent_tags(limit=limit)
        
        # 构建符合TagCloudResponse的返回结构
        return {
            "tags": recent_tags
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{tag_id}", response_model=TagResponse)
@public_endpoint(cache_ttl=300, custom_message="获取标签详情失败")
async def read_tag(
    request: Request,
    tag_id: int
):
    """获取标签详情
    
    获取指定标签的详细信息。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        tag_id: 标签ID
        
    Returns:
        TagResponse: 标签详细信息
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 获取标签详情
        tag = await tag_service.get_tag_detail(tag_id)
        return tag
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.put("/{tag_id}", response_model=TagResponse)
@admin_endpoint(custom_message="更新标签失败")
async def update_tag(
    request: Request,
    tag_id: int,
    tag: tag_schema.TagUpdate
):
    """更新标签信息
    
    更新指定标签的信息。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        tag_id: 标签ID
        tag: 标签更新模型，包含要更新的信息
        
    Returns:
        TagResponse: 更新后的标签信息
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 更新标签
        updated_tag = await tag_service.update_tag(
            tag_id=tag_id,
            data=tag.model_dump(exclude_unset=True)
        )
        return updated_tag
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{tag_id}")
@admin_endpoint(custom_message="删除标签失败")
async def delete_tag(
    request: Request,
    tag_id: int
):
    """删除标签
    
    删除指定的标签（软删除）。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        tag_id: 要删除的标签ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当标签不存在或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 删除标签
        result = await tag_service.delete_tag(tag_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{tag_id}/restore")
@admin_endpoint(custom_message="恢复标签失败")
async def restore_tag(
    request: Request,
    tag_id: int
):
    """恢复已删除的标签
    
    恢复指定的已删除标签。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复标签
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        tag_id: 要恢复的标签ID
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当标签不存在、未被删除或权限不足时抛出相应错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 恢复标签
        result = await tag_service.restore_tag(tag_id)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{tag_id}/update-stats", response_model=TagWithPostsResponse)
@admin_endpoint(custom_message="更新标签统计信息失败")
async def update_tag_statistics(
    request: Request,
    tag_id: int
):
    """更新标签统计信息
    
    更新指定标签的使用统计信息。
    包括：
    1. 使用次数
    2. 最后使用时间
    3. 相关帖子数量
    
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        tag_id: 标签ID
        
    Returns:
        TagWithPostsResponse: 更新后的标签信息，包含最新统计数据和相关帖子
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误，当权限不足时抛出403错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 更新标签统计信息
        updated_tag = await tag_service.update_tag_stats(tag_id)
        return updated_tag
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{tag_id}/posts", response_model=PostListResponse)
@public_endpoint(cache_ttl=300, custom_message="获取标签帖子失败")
async def get_tag_posts(
    request: Request,
    tag_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取标签的所有帖子
    
    获取带有指定标签的所有帖子，支持分页。
    此接口对所有用户开放，结果将被缓存5分钟。
    
    Args:
        request: FastAPI请求对象
        tag_id: 标签ID
        skip: 跳过的记录数，用于分页
        limit: 每页记录数，默认20条
        
    Returns:
        PostListResponse: 帖子列表
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 获取标签帖子
        posts, total = await tag_service.get_posts_by_tag(
            tag_id=tag_id,
            skip=skip,
            limit=limit
        )
        
        # 构建符合PostListResponse的返回结构
        return {
            "posts": posts,
            "total": total
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/search", response_model=TagListResponse)
@public_endpoint(cache_ttl=300, custom_message="搜索标签失败")
async def search_tags(
    request: Request,
    q: str,
    skip: int = 0,
    limit: int = 20
):
    """搜索标签
    
    根据关键词搜索标签，支持分页。
    此接口对所有用户开放，结果将被缓存5分钟。
    
    Args:
        request: FastAPI请求对象
        q: 搜索关键词
        skip: 跳过的记录数，用于分页
        limit: 每页记录数，默认20条
        
    Returns:
        TagListResponse: 标签列表
        
    Raises:
        HTTPException: 当搜索失败时抛出相应错误
    """
    try:
        # 使用Service架构
        tag_service = TagService()
        
        # 搜索标签
        tags, total = await tag_service.search_tags(
            query=q,
            skip=skip,
            limit=limit
        )
        
        # 构建符合TagListResponse的返回结构
        return {
            "tags": tags,
            "total": total
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        ) 