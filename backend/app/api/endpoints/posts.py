from fastapi import APIRouter, HTTPException, Request, Query, Depends, Body, Path, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ...schemas.post import VoteType
from ...schemas import post as post_schema
from ...services.comment_service import CommentService
from ...core.decorators import public_endpoint, admin_endpoint, owner_endpoint
from ...services.favorite_service import FavoriteService
from ...services import PostService
from ...services.post_service import get_post_service
from ...services import get_favorite_service, get_comment_service
from ...core.exceptions import (
    NotFoundError, 
    RequestDataError,
    AuthenticationError,
    BusinessException,
    with_error_handling
)
from ..responses.post import (
    PostResponse, 
    PostDetailResponse,
    PostListResponse,
    PostCommentResponse,
    PostStatsResponse,
    PostDeleteResponse,
    PostVoteResponse,
    PostFavoriteResponse
)
from ...core.auth import get_current_user_optional, get_current_active_user
from ...db.models import User, VoteType

logger = logging.getLogger(__name__)

router = APIRouter()

@with_error_handling(default_error_message="获取帖子作者信息失败")
async def get_post_owner(post_id: int, post_service: PostService = Depends(get_post_service)) -> int:
    """获取帖子作者ID
    
    用于权限验证，获取指定帖子的作者ID。
    
    Args:
        post_id: 帖子ID
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        int: 帖子作者的用户ID
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    # 获取帖子详情
    post = await post_service.get_post_detail(post_id)
    if not post:
        raise NotFoundError(code="post_not_found", message="帖子不存在")
    
    author_id = post.get("author_id")
    if not author_id:
        raise RequestDataError(code="incomplete_post_data", message="帖子数据不完整")
    
    return author_id

@router.post("", response_model=PostResponse)
@public_endpoint(auth_required=True, custom_message="创建帖子失败")
@with_error_handling(default_error_message="创建帖子失败")
async def create_post(
    request: Request,
    post: post_schema.PostCreate,
    post_service: PostService = Depends(get_post_service)
):
    """创建新帖子
    
    创建新的帖子记录，需要用户认证。
    
    包含以下特性：
    1. 用户认证：需要有效的访问令牌
    2. 标签处理：自动处理帖子与标签的关联
    3. 异常处理：使用统一的异常处理装饰器
    
    Args:
        request: FastAPI请求对象
        post: 帖子创建模型，包含标题、内容、分类等
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        Post: 创建成功的帖子信息
        
    Raises:
        HTTPException: 当权限不足或数据验证失败时抛出相应错误
    """
    try:
        # 从token获取当前用户ID
        current_user_id = request.state.user.get("id")
        if not current_user_id:
            raise AuthenticationError(code="missing_user_id", message="无法获取用户ID")
        
        # 准备帖子数据
        try:
            post_data = post.model_dump()
        except AttributeError:
            try:
                post_data = post.dict()
            except AttributeError:
                post_data = {k: v for k, v in post.__dict__.items() if not k.startswith('_')}
        
        # 如果未提供作者ID，使用当前用户ID
        if "author_id" not in post_data or not post_data["author_id"]:
            post_data["author_id"] = current_user_id
        
        # 基本验证
        if not post_data.get("title") or len(post_data.get("title", "")) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "标题不能为空且长度至少为3个字符", "code": "invalid_title"}
            )
        
        if not post_data.get("content"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "内容不能为空", "code": "invalid_content"}
            )
            
        if not post_data.get("category_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail={"message": "必须选择分类", "code": "missing_category"}
            )
            
        if not post_data.get("section_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "必须选择版块", "code": "missing_section"}
            )
        
        # 使用PostService的create_post方法创建帖子，包括处理标签关联
        created_post = await post_service.create_post(post_data)
        
        return created_post
    except BusinessException as be:
        # 业务异常处理
        if hasattr(be, 'status_code') and be.status_code:
            status_code = be.status_code
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail={"message": be.message if hasattr(be, 'message') else str(be), 
                   "code": be.code if hasattr(be, 'code') else "business_error"}
        )
    except Exception as e:
        logger.error(f"创建帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"创建帖子失败: {str(e)}", "code": "create_post_error"}
        )

@router.get("", response_model=PostListResponse)
@public_endpoint(cache_ttl=30, custom_message="获取帖子列表失败")
@with_error_handling(default_error_message="获取帖子列表失败")
async def read_posts(
    request: Request,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    include_hidden: bool = False,
    category_id: Optional[int] = Query(None, ge=1),
    section_id: Optional[int] = Query(None, ge=1),
    author_id: Optional[int] = Query(None, ge=1),
    tag_ids: Optional[List[int]] = Query(None),
    sort_by: Optional[str] = Query(None, regex="^[a-zA-Z0-9_]+$", description="排序字段"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="排序方向(asc或desc)"),
    post_service: PostService = Depends(get_post_service),
):
    """获取帖子列表
    
    提供帖子列表，支持分页、排序和多种筛选条件。
    
    Args:
        request: FastAPI请求对象
        skip: 跳过的记录数，用于分页
        limit: 返回的记录数，用于分页
        include_hidden: 是否包含隐藏的帖子
        category_id: 按分类ID筛选
        section_id: 按版块ID筛选
        author_id: 按作者ID筛选
        tag_ids: 按标签ID列表筛选
        sort_by: 排序字段
        sort_order: 排序方向
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostListResponse: 包含帖子列表和分页信息的响应
    """
    try:
        # 验证排序字段
        valid_sort_fields = ["id", "title", "created_at", "updated_at", "vote_count", "view_count"]
        if sort_by and sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": f"无效的排序字段，允许值: {', '.join(valid_sort_fields)}",
                    "code": "invalid_sort_field"
                }
            )
        
        # 验证排序方向
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "无效的排序方向，允许值: asc, desc",
                    "code": "invalid_sort_order"
                }
            )
        
        # 验证分页参数
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "分页偏移量不能为负数", "code": "invalid_skip"}
            )
            
        if limit < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "每页记录数必须大于0", "code": "invalid_limit"}
            )
            
        if limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "每页记录数不能超过1000", "code": "limit_too_large"}
            )
        
        # 获取帖子列表
        posts, total = await post_service.get_posts(
            skip=skip,
            limit=limit,
            include_hidden=include_hidden,
            category_id=category_id,
            section_id=section_id,
            author_id=author_id,
            tag_ids=tag_ids,
            sort_field=sort_by,
            sort_order=sort_order
        )
        
        return {
            "posts": posts,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except HTTPException:
        raise
    except BusinessException as be:
        # 业务异常处理
        if hasattr(be, 'status_code') and be.status_code:
            status_code = be.status_code
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail={"message": be.message if hasattr(be, 'message') else str(be), 
                   "code": be.code if hasattr(be, 'code') else "business_error"}
        )
    except Exception as e:
        logger.error(f"获取帖子列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"获取帖子列表失败: {str(e)}", "code": "get_posts_error"}
        )

@router.get("/{post_id}", response_model=PostDetailResponse)
@public_endpoint(cache_ttl=30, custom_message="获取帖子详情失败")
@with_error_handling(default_error_message="获取帖子详情失败")
async def read_post(
    post_id: int = Path(..., ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    post_service: PostService = Depends(get_post_service),
):
    """获取帖子详情
    
    获取指定ID帖子的详细信息，包括标签、作者等相关数据。
    
    Args:
        post_id: 帖子ID
        current_user: 当前用户对象（可选）
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostDetailResponse: 包含帖子详情的响应
        
    Raises:
        HTTPException: 当帖子不存在或用户无权查看时抛出相应错误
    """
    try:
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id=post_id)
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "帖子不存在", "code": "post_not_found"}
            )
        
        # 检查权限
        if post.get("is_hidden", False):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"message": "帖子不存在", "code": "post_not_found"}
                )
                
            can_view_hidden = hasattr(current_user, 'permissions') and any(
                perm in current_user.permissions for perm in ["manage_content", "manage_system"]
            )
            
            if not can_view_hidden and post.get("author_id") != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"message": "帖子不存在", "code": "post_not_found"}
                )
        
        # 确保所有必要的字段都存在，防止前端渲染错误
        if "tags" not in post:
            post["tags"] = []
        if "comments" not in post:
            post["comments"] = []
        
        # 添加PostDetailResponse需要的字段
        if "view_count" not in post:
            post["view_count"] = 0
        if "favorite_count" not in post:
            post["favorite_count"] = 0
        
        # 添加tag_ids字段，用于ID引用模式
        tag_ids = []
        if post.get("tags"):
            tag_ids = [tag.get("id") for tag in post["tags"] if tag.get("id")]
        post["tag_ids"] = tag_ids
        
        # 尝试记录浏览量增加（不阻塞响应）
        try:
            # 异步记录浏览量，不等待结果
            post_service.increment_view_count(post_id, background=True)
        except Exception as view_exc:
            # 记录但不影响主请求
            logger.warning(f"记录帖子浏览量失败: {str(view_exc)}")
        
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取帖子详情失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"获取帖子详情失败: {str(e)}", "code": "get_post_detail_error"}
        )

@router.put("/{post_id}", response_model=PostResponse)
@owner_endpoint(custom_message="更新帖子失败", resource_owner_lookup_func=get_post_owner)
@with_error_handling(default_error_message="更新帖子失败")
async def update_post(
    request: Request,
    post_id: int,
    post: post_schema.PostUpdate,
    post_service: PostService = Depends(get_post_service)
):
    """更新帖子
    
    更新指定ID的帖子信息，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post: 更新的帖子数据
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        Post: 更新后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    # 获取当前用户ID
    current_user_id = request.state.user.get("id")
    
    # 获取帖子详情，检查是否存在
    existing_post = await post_service.get_post_detail(post_id)
    if not existing_post:
        raise NotFoundError(code="post_not_found", message="帖子不存在")
        
    # 更新帖子内容
    # 兼容不同版本的Pydantic，尝试使用dict()或model_dump()
    try:
        post_data = post.model_dump(exclude_unset=True)
    except AttributeError:
        try:
            post_data = post.dict(exclude_unset=True)
        except AttributeError:
            post_data = {k: v for k, v in post.__dict__.items() if not k.startswith('_')}
    
    updated_post = await post_service.update_post(post_id, post_data)
    
    return updated_post

@router.delete("/{post_id}", response_model=PostDeleteResponse)
@owner_endpoint(custom_message="删除帖子失败", resource_owner_lookup_func=get_post_owner)
@with_error_handling(default_error_message="删除帖子失败")
async def delete_post(
    request: Request,
    post_id: int,
    post_service: PostService = Depends(get_post_service)
):
    """删除帖子
    
    软删除指定的帖子，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    # 记录操作
    user_id = request.state.user.get("id")
    
    # 删除帖子
    success = await post_service.delete_post(post_id)
    
    if success:
        return {"message": "帖子已成功删除", "post_id": post_id}
    else:
        logger.warning(f"删除帖子 {post_id} 失败")
        raise HTTPException(status_code=500, detail={"message": "删除帖子失败", "error_code": "DELETE_FAILED"})

@router.post("/{post_id}/restore", response_model=PostResponse)
@admin_endpoint(custom_message="恢复帖子失败")
@with_error_handling(default_error_message="恢复帖子失败")
async def restore_post(
    request: Request,
    post_id: int,
    post_service: PostService = Depends(get_post_service)
):
    """恢复已删除的帖子
    
    恢复指定的已删除帖子，仅允许版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    # 恢复帖子
    restored_post = await post_service.restore_post(post_id)
    
    return {
        "message": "帖子已成功恢复",
        "post_id": post_id,
        "post": restored_post
    }

@router.patch("/{post_id}/visibility", response_model=PostResponse)
@owner_endpoint(custom_message="切换帖子可见性失败", resource_owner_lookup_func=get_post_owner)
@with_error_handling(default_error_message="切换帖子可见性失败")
async def toggle_post_visibility(
    request: Request,
    post_id: int,
    visibility: dict = Body(...),
    post_service: PostService = Depends(get_post_service)
):
    """切换帖子可见性
    
    切换指定帖子的可见性状态，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        visibility: 包含可见性设置的字典
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        Post: 更新后的帖子信息
    """
    
    # 获取帖子详情，检查是否存在
    existing_post = await post_service.get_post_detail(post_id)
    if not existing_post:
        raise NotFoundError(code="post_not_found", message="帖子不存在")
    
    # 更新帖子可见性
    is_hidden = visibility.get("hidden", not existing_post.get("is_hidden", False))
    
    updated_post = await post_service.toggle_visibility(post_id, is_hidden)
    
    return updated_post

@router.post("/{post_id}/vote", response_model=PostVoteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="点赞操作失败")
@with_error_handling(default_error_message="点赞操作失败")
async def vote_post(
    post_id: int = Path(..., ge=1),
    vote_data: post_schema.PostVoteCreate = Body(...),
    request: Request = None,
    post_service: PostService = Depends(get_post_service)
):
    """
    为帖子投票（赞同或反对）
    
    Args:
        post_id: 帖子ID
        vote_data: 投票数据，包含vote_type字段
        request: FastAPI请求对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostVoteResponse: 包含投票结果的响应
    """
    try:
        # 获取当前用户信息并验证
        current_user = request.state.user
        user_id = current_user.get("id")
        if not user_id:
            raise AuthenticationError(code="missing_user_id", message="未能获取用户ID")
        
        # 记录投票数据
        logger.info(f"Vote data: {vote_data}")
        logger.info(f"Vote type: {vote_data.vote_type}")
        logger.info(f"Vote type type: {type(vote_data.vote_type)}")
        
        # 验证投票类型
        vote_type_str = str(vote_data.vote_type)
        if vote_type_str not in ["upvote", "downvote"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "无效的投票类型，只允许 upvote 或 downvote", "code": "invalid_vote_type"}
            )
        
        # 验证帖子是否存在
        post_exists = await post_service.get_post_detail(post_id)
        if not post_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "帖子不存在或已删除", "code": "post_not_found"}
            )
        
        # 将字符串转换为枚举
        vote_type = VoteType.UPVOTE if vote_type_str == "upvote" else VoteType.DOWNVOTE
        
        # 执行投票
        vote_result = await post_service.vote_post(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_type
        )
        
        # 检查返回结果
        if vote_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "帖子不存在或已删除", "code": "post_not_found"}
            )
        
        # 确保结果符合响应模型
        processed_result = {
            "post_id": vote_result.get("post_id"),
            "upvotes": vote_result.get("upvotes", 0),
            "downvotes": vote_result.get("downvotes", 0),
            "score": vote_result.get("score", 0),
            "user_vote": vote_result.get("user_vote"),
            "action": vote_result.get("action", "")
        }
        
        return processed_result
    except HTTPException:
        raise
    except BusinessException as be:
        # 业务异常处理
        if hasattr(be, 'status_code') and be.status_code:
            status_code = be.status_code
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail={"message": be.message if hasattr(be, 'message') else str(be), 
                   "code": be.code if hasattr(be, 'code') else "business_error"}
        )
    except Exception as e:
        logger.error(f"投票操作失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"投票操作失败: {str(e)}", "code": "vote_error"}
        )

@router.get("/{post_id}/votes", response_model=PostStatsResponse)
@public_endpoint(cache_ttl=10, custom_message="获取投票数失败")
@with_error_handling(default_error_message="获取投票数失败")
async def get_vote_count(
    request: Request,
    post_id: int,
    post_service: PostService = Depends(get_post_service)
):
    """获取帖子的点赞数
    
    提供帖子的当前点赞计数。
    
    包含以下特性：
    1. 缓存：结果缓存10秒
    2. 异常处理：使用统一的异常处理装饰器
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostStatsResponse: 包含点赞数和帖子ID的响应
    """
    
    # 获取点赞数
    count = await post_service.get_vote_count(post_id)
    
    
    return {
        "post_id": post_id,
        "vote_count": count
    }

@router.post("/{post_id}/favorite", response_model=PostFavoriteResponse)
@public_endpoint(auth_required=True, custom_message="收藏帖子失败")
@with_error_handling(default_error_message="收藏帖子失败")
async def favorite_post(
    request: Request,
    post_id: int,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """收藏帖子
    
    将指定帖子添加到当前用户的收藏列表。
    
    包含以下特性：
    1. 用户认证：需要有效的访问令牌
    2. 防重复：若已收藏，不会创建重复记录
    3. 异常处理：使用统一的异常处理装饰器
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        PostFavoriteResponse: 包含收藏状态和收藏ID的响应
    """
    
    # 验证用户信息
    if not hasattr(request.state, 'user') or not request.state.user:
        raise AuthenticationError(code="not_authenticated", message="需要登录才能收藏")
    
    # 从token中获取用户ID
    user_id = request.state.user.get("id")
    if not user_id:
        raise AuthenticationError(code="missing_user_id", message="无法获取用户ID")
        
    # 验证帖子是否存在
    post_exists = await favorite_service.check_post_exists(post_id)
    if not post_exists:
        raise NotFoundError(code="post_not_found", message="帖子不存在或已删除")
    
    # 检查是否已收藏
    try:
        is_favorited = await favorite_service.is_post_favorited(post_id, user_id)
        if is_favorited:
            # 已收藏，返回当前收藏信息而不是报错
            favorite = await favorite_service.get_favorite(post_id, user_id)
            
            return {
                "post_id": post_id,
                "user_id": user_id,
                "status": "already_favorited",
                "favorite_id": favorite.get("id"),
                "created_at": favorite.get("created_at")
            }
    except Exception as check_error:
        # 检查异常不中断主流程，只记录日志
        logger.warning(f"检查收藏状态时出错: {str(check_error)}")
    
    # 收藏帖子
    favorite = await favorite_service.favorite_post(post_id, user_id)
    
    return {
        "post_id": post_id,
        "user_id": user_id,
        "status": "favorited",
        "favorite_id": favorite.get("id"),
        "created_at": favorite.get("created_at")
    }

@router.delete("/{post_id}/favorite", response_model=PostFavoriteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="取消收藏操作失败")
@with_error_handling(default_error_message="取消收藏操作失败")
async def unfavorite_post(
    request: Request,
    post_id: int,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """取消收藏帖子
    
    从当前用户的收藏列表中移除指定帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要取消收藏的帖子ID
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        FavoriteResponse: 取消收藏操作结果
        
    Raises:
        HTTPException: 当用户未登录或操作失败时抛出相应错误
    """
    # 获取当前用户ID
    if not request.state.user:
        raise HTTPException(status_code=401, detail="需要登录才能操作收藏")
    
    user_id = request.state.user.get("id")
    
    # 移除收藏
    result = await favorite_service.remove_favorite(post_id, user_id)
    
    # 格式化返回结果
    return {
        "post_id": post_id,
        "user_id": user_id,
        "status": "unfavorited",
        "favorite_id": None,
        "created_at": None
    }

@router.get("/{post_id}/favorite/status", response_model=bool)
@public_endpoint(auth_required=True, cache_ttl=10, custom_message="获取收藏状态失败")
@with_error_handling(default_error_message="获取收藏状态失败")
async def check_favorite_status(
    request: Request,
    post_id: int,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """检查当前用户是否已收藏指定帖子
    
    返回布尔值，表示当前用户是否已收藏该帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要检查的帖子ID
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        bool: 如果用户已收藏该帖子则返回True，否则返回False
    """
    # 验证用户身份
    if not hasattr(request.state, 'user') or not request.state.user:
        # 未登录用户默认返回未收藏状态，而不是抛出异常
        return False
    
    user_id = request.state.user.get("id")
    if not user_id:
        return False
        
    
    # 验证帖子是否存在
    try:
        # 检查收藏状态前验证帖子存在性
        post_exists = await favorite_service.check_post_exists(post_id)
        if not post_exists:
            # 返回False而不是抛出异常，更符合前端预期
            return False
    except Exception as post_check_error:
        # 如果验证帖子失败，记录错误但继续处理
        logger.warning(f"验证帖子存在性失败: {str(post_check_error)}")
    
    # 检查收藏状态
    is_favorited = await favorite_service.is_post_favorited(post_id, user_id)
    
        
    return is_favorited

@router.get("/{post_id}/comments", response_model=PostCommentResponse)
@public_endpoint(cache_ttl=5, custom_message="获取帖子评论失败")
@with_error_handling(default_error_message="获取帖子评论失败")
async def read_post_comments(
    request: Request,
    post_id: int, 
    skip: int = 0, 
    limit: int = 10,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    include_deleted: bool = False,
    comment_service: CommentService = Depends(get_comment_service)
):
    """获取帖子的评论列表
    
    返回指定帖子的评论列表，支持分页和排序。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        skip: 跳过的记录数量，用于分页
        limit: 返回的记录数量，用于分页
        sort_by: 排序字段，默认为创建时间
        sort_order: 排序方向，desc为降序，asc为升序
        include_deleted: 是否包含已删除的评论，默认为False
        comment_service: 评论服务实例（通过依赖注入获取）
        
    Returns:
        PostCommentResponse: 包含评论列表和分页信息的响应
    """
    # 检查当前用户角色，判断是否可以查看已删除的评论
    user_role = None
    if hasattr(request.state, 'user') and request.state.user:
        user_role = request.state.user.get("role", "user")
    
    # 只有管理员可以看到已删除的评论
    if include_deleted and user_role not in ["admin", "super_admin", "moderator"]:
        include_deleted = False
        
    try:
        # 获取评论列表
        comments, total = await comment_service.get_post_comments(
            post_id=post_id, 
            skip=skip, 
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted
        )
        
        return {
            "comments": comments,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "post_id": post_id
        }
    except NotFoundError:
        # 找不到帖子时，返回空列表而不是报错
        return {
            "comments": [],
            "total": 0,
            "page": 1,
            "size": limit,
            "post_id": post_id
        }