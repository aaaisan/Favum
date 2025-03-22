from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional

from ...schemas.inputs import user as user_schema
# from ...schemas.inputs import post as post_schema
from ...services import UserService, PostService, FavoriteService
from ...dependencies import get_favorite_service, get_user_service, get_post_service
from ...core.decorators import public_endpoint, admin_endpoint, owner_endpoint
from ...core.enums import Role, Permission
from ...core.exceptions import APIError, BusinessException, NotFoundError
from ...core.logging import get_logger
from ...db.models.user import User
from ...core.auth import get_current_user
from ...core.decorators.error import handle_exceptions, with_error_handling

from ...schemas.responses.user import (
    UserResponse, 
    UserProfileResponse, 
    UserListResponse, 
    UserDeleteResponse,
)
from ...schemas.responses.post import PostListResponse

# 创建logger实例
logger = get_logger(__name__)

router = APIRouter()

@router.post("", response_model=UserResponse)
@admin_endpoint(custom_message="创建用户失败")
async def create_user(
    # request: Request,
    user: user_schema.UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """创建新用户
    
    user_service = UserService()
    注册一个新用户账号。
    包含以下特性：
    1. 异常处理：自动处理数据库异常和业务异常
    2. 速率限制：每小时最多创建20个用户
    3. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        user: 用户创建模型，包含用户信息
        
    Returns:
        UserResponse: 创建成功的用户信息
        
    Raises:
        HTTPException: 当用户名或邮箱已存在、或创建过程中出现其他错误时抛出
    """
    try:
        result = await user_service.create_user(user.model_dump())
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("", response_model=UserListResponse)
@public_endpoint(auth_required=True, custom_message="获取用户列表失败")
async def read_users(
    # request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: Optional[str] = None,
    order: str = "asc",
    user_service: UserService = Depends(get_user_service)
):
    """获取用户列表
    
    Args:
        request: 请求对象
        skip: 分页偏移量
        limit: 每页数量
        sort: 排序字段
        order: 排序方向 ("asc"或"desc")
        
    Returns:
        包含用户列表和总数的响应
    """
    try:
        # 从请求中获取用户信息
        # user_info = request.state.user
        
        # 从数据库获取用户列表
        users, total = await user_service.get_users(skip, limit, sort, order)
        
        # 处理用户数据，确保日期时间字段为字符串格式
        processed_users = []
        for user in users:
            # 确保日期时间字段格式化为字符串
            if user.get("created_at") and not isinstance(user.get("created_at"), str):
                user["created_at"] = user["created_at"].isoformat()
                
            if user.get("updated_at") and not isinstance(user.get("updated_at"), str):
                user["updated_at"] = user["updated_at"].isoformat()
                
            processed_users.append(user)
        
        # 返回用户列表和总数
        return {"users": processed_users, "total": total}
    except BusinessException as e:
        # 处理业务异常
        logger.error(f"业务错误: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get("/me", response_model=UserResponse)
@public_endpoint(auth_required=True, custom_message="获取当前用户信息失败")
# @handle_exceptions(default_error_message="获取当前用户信息失败")
async def read_user_me(
    request: Request,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取当前登录用户的信息
    
    返回当前登录用户的详细信息。
    
    Args:
        request: FastAPI请求对象
        user: 当前用户对象
        user_service: 用户服务实例（通过依赖注入获取）
        
    Returns:
        UserResponse: 当前用户的详细信息
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "未登录", "code": "not_authenticated"}
        )
    
    # 获取用户详细信息
    user_detail = await user_service.get_user_detail(user.id)
    if not user_detail:
        raise NotFoundError(code="user_not_found", message="用户不存在")
    
    return user_detail

@router.get("/{user_id}", response_model=UserResponse)
@public_endpoint(cache_ttl=60, custom_message="获取用户详情失败")
async def read_user(
    # request: Request,
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """获取指定用户详情
    
    user_service = UserService()
    获取指定用户ID的详细信息。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        
    Returns:
        UserResponse: 用户详情
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
    """
    try:
        
        # 获取用户详情
        user = await user_service.get_user_by_id(user_id)

        # 直接返回用户数据
        return user
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )

@router.put("/{user_id}", response_model=UserResponse)
@owner_endpoint(owner_param_name="user_id", custom_message="更新用户信息失败")
async def update_user(
    request: Request,
    user_id: int,
    user_update: user_schema.UserSchema,
    user_service: UserService = Depends(get_user_service)
):
    """更新用户信息
    
    user_service = UserService()
    更新指定用户的信息。
    用户只能更新自己的信息，管理员可以更新任何用户的信息。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        user_update: 用户更新信息模型
        
    Returns:
        UserResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 当用户不存在、权限不足或令牌无效时抛出相应错误
        BusinessException: 当更新的邮箱已被其他用户使用时抛出
    """
    try:
        
        # 获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 更新用户信息
        updated_user = await user_service.update_user(
            user_id=user_id,
            user_data=user_update.model_dump(exclude_unset=True),
            current_user_id=current_user_id
        )

        return user_service.model_to_dict(updated_user)
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.delete("/{user_id}", response_model=UserDeleteResponse)
@admin_endpoint(custom_message="删除用户失败")
async def delete_user(
    request: Request,
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """删除用户（软删除）
    
    user_service = UserService()
    将用户标记为已删除状态（软删除）。
    用户只能删除自己的账号，管理员可以删除任何用户。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        
    Returns:
        UserDeleteResponse: 包含操作结果消息
        
    Raises:
        HTTPException: 当用户不存在、权限不足或令牌无效时抛出相应错误
    """
    try:
        
        # 获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 删除用户
        await user_service.delete_user(user_id=user_id, current_user_id=current_user_id)
        
        # 构建符合UserDeleteResponse的返回结构
        return {
            "id": user_id,
            "message": "用户已成功删除"
        }
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

@router.post("/{user_id}/restore", response_model=UserResponse)
@admin_endpoint(custom_message="恢复用户失败")
async def restore_user(
    # request: Request,
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """恢复已删除用户
    
    user_service = UserService()
    恢复软删除状态的用户账号。
    仅管理员可执行此操作。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        
    Returns:
        UserResponse: 恢复后的用户信息
        
    Raises:
        HTTPException: 当用户不存在、已处于激活状态或令牌无效时抛出相应错误
    """
    try:
        
        # 恢复用户
        restored_user = await user_service.restore_user(user_id)

        return user_service.model_to_dict(restored_user)
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/me/profile", response_model=UserProfileResponse)
@public_endpoint(auth_required=True, custom_message="获取个人资料失败")
async def read_user_profile(
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """获取当前用户的个人资料
    
    user_service = UserService()
    获取当前登录用户的详细资料，包括统计信息。
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        UserProfileResponse: 用户个人资料
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
    """
    try:
        
        # 获取当前用户ID
        user_id = request.state.user.get("id")
        
        # 获取用户详情
        profile = await user_service.get_user_profile(user_id)

        return user_service.model_to_dict(profile)
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{user_id}/posts", response_model=PostListResponse)
@public_endpoint(auth_required=True, custom_message="获取用户帖子失败")
async def read_user_posts(
    # request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    user_service: UserService = Depends(get_user_service),
    post_service: PostService = Depends(get_post_service)
):
    """获取用户发布的帖子列表
    
    user_service = UserService()
    按照发布时间倒序返回指定用户发布的帖子列表。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认20
        
    Returns:
        PostListResponse: 包含帖子列表的响应对象
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
    """
    try:
        posts, total = await user_service.get_user_posts(user_id=user_id, skip=skip, limit=limit)
        
        # 处理帖子数据，确保日期时间字段为字符串格式
        processed_posts = []
        for post in posts:
            processed_post = post_service.model_to_dict(post)
            processed_posts.append(processed_post)
        
        # 构建符合PostListResponse的返回结构
        return {
            "posts": processed_posts,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except Exception as e:
        logger.error(f"Error retrieving user posts for user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户帖子失败"
        )

@router.get("/me/favorites", response_model=PostListResponse)
@public_endpoint(auth_required=True, custom_message="获取收藏列表失败")
@with_error_handling(default_error_message="获取收藏列表失败")
async def get_my_favorites(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
    post_service: PostService = Depends(get_post_service)
):
    """获取当前用户的收藏列表
    
    返回当前登录用户收藏的帖子列表。
    
    Args:
        request: FastAPI请求对象
        skip: 跳过的记录数量，用于分页
        limit: 返回的记录数量，用于分页
        user: 当前用户对象
        favorite_service: 收藏服务实例（通过依赖注入获取）
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostListResponse: 包含收藏帖子列表和分页信息的响应
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "未登录", "code": "not_authenticated"}
        )
    
    # 获取收藏列表
    favorites, total = await favorite_service.get_user_favorites(
        user_id=user.id,
        skip=skip,
        limit=limit
    )
    
    # 获取帖子详情
    post_ids = [fav.get("post_id") for fav in favorites]
    posts = await post_service.get_posts_by_ids(post_ids)
    
    return {
        "posts": posts,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit
    }

@router.get("/{user_id}/favorites", response_model=PostListResponse)
@public_endpoint(cache_ttl=60, custom_message="获取用户收藏列表失败")
@with_error_handling(default_error_message="获取用户收藏列表失败")
async def get_user_favorites(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    user: Optional[User] = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
    post_service: PostService = Depends(get_post_service)
):
    """获取指定用户的收藏列表
    
    返回指定用户收藏的帖子列表。
    
    Args:
        request: FastAPI请求对象
        user_id: 要查看收藏的用户ID
        skip: 跳过的记录数量，用于分页
        limit: 返回的记录数量，用于分页
        user: 当前用户对象(可选)
        favorite_service: 收藏服务实例（通过依赖注入获取）
        post_service: 帖子服务实例（通过依赖注入获取）
        
    Returns:
        PostListResponse: 包含收藏帖子列表和分页信息的响应
    """
    # 获取收藏列表
    favorites, total = await favorite_service.get_user_favorites(
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    # 获取帖子详情
    post_ids = [fav.get("post_id") for fav in favorites]
    posts = await post_service.get_posts_by_ids(post_ids)
    
    return {
        "posts": posts,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit
    }
