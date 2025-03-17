from fastapi import APIRouter, HTTPException, Request, Query, Depends, Body, Path, status
from typing import List, Optional, Dict, Any
from datetime import datetime
# import logging

# from ...schemas.inputs.post import VoteType
from ...schemas.inputs import post as post_schema
from ...services.comment_service import CommentService
from ...core.decorators import public_endpoint, admin_endpoint, owner_endpoint
from ...services.favorite_service import FavoriteService
from ...services import PostService
from ...dependencies import get_post_service, get_favorite_service, get_comment_service
from ...core.exceptions import (
    NotFoundError, 
    RequestDataError,
    AuthenticationError,
    BusinessException
)
from ...core.decorators.error import with_error_handling
from ...schemas.responses.post import (
    PostResponse, 
    PostDetailResponse,
    PostListResponse,
    PostCommentResponse,
    PostStatsResponse,
    PostDeleteResponse,
    PostVoteResponse,
    PostFavoriteResponse
)
from ...core.auth import get_current_user
from ...core.permissions import require_active_user
from ...db.models import User, VoteType
from ...core.logging import get_logger

logger = get_logger(__name__) 

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
@public_endpoint(auth_required=True, custom_message="创建帖子失败", rate_limit_count=20)
@with_error_handling(default_error_message="创建帖子失败")
async def create_post(
    request: Request,
    post: post_schema.PostCreate,
    user: User = Depends(get_current_user),
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
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        Post: 创建成功的帖子信息
        
    Raises:
        HTTPException: 当权限不足或数据验证失败时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
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
            post_data["author_id"] = user.id
        
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
    user: Optional[User] = Depends(get_current_user),
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
        user: 当前用户对象(可选)
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
            detail={"message": f"获取帖子列表失败: {str(e)}", "code": "list_posts_error"}
        )

@router.get("/{post_id}", response_model=PostDetailResponse)
@public_endpoint(cache_ttl=300, custom_message="获取帖子详情失败")
@with_error_handling(default_error_message="获取帖子详情失败")
async def read_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要获取的帖子ID"),
    user: Optional[User] = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """获取帖子详情
    
    获取指定ID的帖子详细信息。
    
    Args:
        post_id: 帖子ID
        user: 当前用户对象(可选)
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostDetailResponse: 帖子详细信息
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    # 获取帖子详情
    post = await post_service.get_post_detail(post_id)
    if not post:
        raise NotFoundError(code="post_not_found", message="帖子不存在")
    
    # 如果帖子已隐藏且当前用户不是作者或管理员，则不允许查看
    if post.get("is_hidden", False):
        # 未登录用户不能查看隐藏帖子
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "没有权限查看此帖子", "code": "post_hidden"}
            )
            
        # 检查是否为作者或管理员
        is_author = user.id == post.get("author_id")
        is_admin = user.role == "admin"
        
        if not (is_author or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "没有权限查看此帖子", "code": "post_hidden"}
            )
    
    return post

@router.put("/{post_id}", response_model=PostResponse)
@owner_endpoint(
    owner_id_func=get_post_owner,
    custom_message="更新帖子失败",
    rate_limit_count=20
)
@with_error_handling(default_error_message="更新帖子失败")
async def update_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要更新的帖子ID"),
    post: post_schema.PostUpdate = Body(...),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """更新帖子
    
    更新指定ID的帖子信息。
    用户只能更新自己的帖子，管理员可以更新任何帖子。
    
    Args:
        post_id: 帖子ID
        post: 帖子更新数据
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostResponse: 更新后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在、权限不足或数据验证失败时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id)
        if not post:
            raise NotFoundError(code="post_not_found", message="帖子不存在")
            
        # 检查权限
        is_author = user.id == post.get("author_id")
        is_admin = user.role == "admin"
        
        if not (is_author or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "没有权限修改此帖子", "code": "permission_denied"}
            )
        
        # 准备更新数据
        try:
            update_data = post.model_dump(exclude_unset=True)
        except AttributeError:
            try:
                update_data = post.dict(exclude_unset=True)
            except AttributeError:
                update_data = {k: v for k, v in post.__dict__.items() if not k.startswith('_')}
        
        # 基本验证
        if "title" in update_data and (not update_data["title"] or len(update_data["title"]) < 3):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "标题不能为空且长度至少为3个字符", "code": "invalid_title"}
            )
            
        if "content" in update_data and not update_data["content"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "内容不能为空", "code": "invalid_content"}
            )
        
        # 更新帖子
        updated_post = await post_service.update_post(post_id, update_data)
        return updated_post
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
        logger.error(f"更新帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"更新帖子失败: {str(e)}", "code": "update_post_error"}
        )

@router.delete("/{post_id}", response_model=PostDeleteResponse)
@owner_endpoint(
    owner_id_func=get_post_owner,
    custom_message="删除帖子失败",
    rate_limit_count=10
)
@with_error_handling(default_error_message="删除帖子失败")
async def delete_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要删除的帖子ID"),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """删除帖子
    
    删除指定ID的帖子。
    用户只能删除自己的帖子，管理员可以删除任何帖子。
    
    Args:
        post_id: 帖子ID
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostDeleteResponse: 删除操作的结果
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
        # 获取帖子详情
        post = await post_service.get_post_detail(post_id)
        if not post:
            raise NotFoundError(code="post_not_found", message="帖子不存在")
            
        # 检查权限
        is_author = user.id == post.get("author_id")
        is_admin = user.role == "admin"
        
        if not (is_author or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "没有权限删除此帖子", "code": "permission_denied"}
            )
        
        # 删除帖子
        await post_service.delete_post(post_id)
        
        return {
            "id": post_id,
            "message": "帖子已成功删除"
        }
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
        logger.error(f"删除帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"删除帖子失败: {str(e)}", "code": "delete_post_error"}
        )

@router.post("/{post_id}/restore", response_model=PostResponse)
@admin_endpoint(custom_message="恢复帖子失败")
@with_error_handling(default_error_message="恢复帖子失败")
async def restore_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要恢复的帖子ID"),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """恢复已删除的帖子
    
    恢复软删除状态的帖子。
    仅管理员可执行此操作。
    
    Args:
        post_id: 帖子ID
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostResponse: 恢复后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在、未被删除或权限不足时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
        # 检查是否为管理员
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "需要管理员权限", "code": "permission_denied"}
            )
        
        # 恢复帖子
        restored_post = await post_service.restore_post(post_id)
        if not restored_post:
            raise NotFoundError(code="post_not_found", message="帖子不存在")
            
        return restored_post
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
        logger.error(f"恢复帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"恢复帖子失败: {str(e)}", "code": "restore_post_error"}
        )

@router.post("/{post_id}/hide", response_model=PostResponse)
@admin_endpoint(custom_message="隐藏帖子失败", rate_limit_count=10)
@with_error_handling(default_error_message="隐藏帖子失败")
async def hide_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要隐藏的帖子ID"),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """隐藏帖子
    
    将帖子标记为隐藏状态。
    仅管理员和版主可执行此操作。
    
    Args:
        post_id: 帖子ID
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostResponse: 隐藏后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
        # 检查是否为管理员或版主
        if user.role not in ["admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "需要管理员或版主权限", "code": "permission_denied"}
            )
        
        # 隐藏帖子
        hidden_post = await post_service.hide_post(post_id)
        if not hidden_post:
            raise NotFoundError(code="post_not_found", message="帖子不存在")
            
        return hidden_post
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
        logger.error(f"隐藏帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"隐藏帖子失败: {str(e)}", "code": "hide_post_error"}
        )

@router.post("/{post_id}/unhide", response_model=PostResponse)
@admin_endpoint(custom_message="取消隐藏帖子失败", rate_limit_count=10)
@with_error_handling(default_error_message="取消隐藏帖子失败")
async def unhide_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要取消隐藏的帖子ID"),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """取消隐藏帖子
    
    将帖子从隐藏状态恢复为可见状态。
    仅管理员和版主可执行此操作。
    
    Args:
        post_id: 帖子ID
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostResponse: 恢复显示后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    try:
        # 检查用户认证和激活状态
        user = require_active_user(user)
        
        # 检查是否为管理员或版主
        if user.role not in ["admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "需要管理员或版主权限", "code": "permission_denied"}
            )
        
        # 取消隐藏帖子
        unhidden_post = await post_service.unhide_post(post_id)
        if not unhidden_post:
            raise NotFoundError(code="post_not_found", message="帖子不存在")
            
        return unhidden_post
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
        logger.error(f"取消隐藏帖子失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"取消隐藏帖子失败: {str(e)}", "code": "unhide_post_error"}
        )

@router.post("/{post_id}/vote", response_model=PostVoteResponse)
@public_endpoint(auth_required=True, custom_message="投票失败", rate_limit_count=50)
@with_error_handling(default_error_message="投票失败")
async def vote_post(
    request: Request,
    post_id: int = Path(..., title="帖子ID", description="要投票的帖子ID"),
    vote_type: VoteType = Body(..., embed=True),
    user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    为帖子投票（赞同或反对）
    
    Args:
        post_id: 帖子ID
        vote_type: 投票类型，包含vote_type字段
        request: FastAPI请求对象
        user: 当前用户对象
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostVoteResponse: 包含投票结果的响应
    """
    try:
        # 获取用户ID
        if not user:
            raise AuthenticationError(code="not_authenticated", message="需要登录才能投票")
        
        # user_id = user.id
        
        # 记录投票数据
        logger.info(f"Vote data: {vote_type}")
        logger.info(f"Vote type: {vote_type.value}")
        logger.info(f"Vote type type: {type(vote_type.value)}")
        
        # 验证投票类型
        vote_type_str = str(vote_type.value)
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
            user_id=user.id,
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
    user: User = Depends(get_current_user),
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
        user: 当前用户对象
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        PostFavoriteResponse: 包含收藏状态和收藏ID的响应
    """
    if not user:
        raise AuthenticationError(code="not_authenticated", message="需要登录才能收藏")
        
    # 验证帖子是否存在
    post_exists = await favorite_service.check_post_exists(post_id)
    if not post_exists:
        raise NotFoundError(code="post_not_found", message="帖子不存在或已删除")
    
    # 检查是否已收藏
    try:
        is_favorited = await favorite_service.is_post_favorited(post_id, user.id)
        if is_favorited:
            # 已收藏，返回当前收藏信息而不是报错
            favorite = await favorite_service.get_favorite(post_id, user.id)
            
            return {
                "post_id": post_id,
                "user_id": user.id,
                "status": "already_favorited",
                "favorite_id": favorite.get("id"),
                "created_at": favorite.get("created_at")
            }
    except Exception as check_error:
        # 检查异常不中断主流程，只记录日志
        logger.warning(f"检查收藏状态时出错: {str(check_error)}")
    
    # 收藏帖子
    favorite = await favorite_service.favorite_post(post_id, user.id)
    
    return {
        "post_id": post_id,
        "user_id": user.id,
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
    user: User = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """取消收藏帖子
    
    从当前用户的收藏列表中移除指定帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要取消收藏的帖子ID
        user: 当前用户对象
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        FavoriteResponse: 取消收藏操作结果
        
    Raises:
        HTTPException: 当用户未登录或操作失败时抛出相应错误
    """
    if not user:
        raise HTTPException(status_code=401, detail="需要登录才能操作收藏")
    
    # 移除收藏
    result = await favorite_service.remove_favorite(post_id, user.id)
    
    # 格式化返回结果
    return {
        "post_id": post_id,
        "user_id": user.id,
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
    user: Optional[User] = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """检查当前用户是否已收藏指定帖子
    
    返回布尔值，表示当前用户是否已收藏该帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 要检查的帖子ID
        user: 当前用户对象(可选)
        favorite_service: 收藏服务实例（通过依赖注入获取）
        
    Returns:
        bool: 如果用户已收藏该帖子则返回True，否则返回False
    """
    # 未登录用户默认返回未收藏状态
    if not user:
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
    is_favorited = await favorite_service.is_post_favorited(post_id, user.id)
    
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
    user: Optional[User] = Depends(get_current_user),
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
        user: 当前用户对象(可选)
        comment_service: 评论服务实例（通过依赖注入获取）
        
    Returns:
        PostCommentResponse: 包含评论列表和分页信息的响应
    """
    # 检查当前用户角色，判断是否可以查看已删除的评论
    user_role = user.role if user else None
    
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