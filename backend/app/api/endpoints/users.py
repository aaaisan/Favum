from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional

from ...schemas import user as user_schema
from ...schemas import post as post_schema
from ...services.favorite_service import FavoriteService
from ...services.user_service import UserService
from ...core.decorators import public_endpoint, admin_endpoint, owner_endpoint
from ...core.enums import Role, Permission
from ...core.exceptions import APIError, BusinessException
from ...core.logging import get_logger
from ...db.models.user import User
from ...core.auth import get_current_active_user

from ..responses import (
    UserResponse, 
    UserProfileResponse, 
    UserListResponse, 
    UserDeleteResponse
)
from ..responses.post import PostListResponse

# 创建logger实例
logger = get_logger(__name__)

router = APIRouter()

@router.post("", response_model=UserResponse)
@admin_endpoint(custom_message="创建用户失败")
async def create_user(
    request: Request,
    user: user_schema.UserCreate
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
        # 创建服务实例
        user_service = UserService()
        
        # 调用服务创建用户
        result = await user_service.create_user(user.model_dump())
        
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("")
@public_endpoint(auth_required=True, custom_message="获取用户列表失败")
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: Optional[str] = None,
    order: str = "asc"
):
    """
    获取用户列表
    
    Args:
        request: 请求对象
        skip: 分页偏移量
        limit: 每页数量
        sort: 排序字段
        order: 排序方向 ("asc"或"desc")
    """
    try:
        # 从请求中获取用户信息
        user_info = request.state.user
        
        # 创建模拟用户列表
        users = [
            {
                "id": 46,
                "username": "admin",
                "email": "admin@example.com",
                "bio": "测试更新个人简介",
                "avatar_url": "https://example.com/avatars/new.jpg",
                "is_active": True,
                "role": "admin",
                "created_at": "2025-03-05 18:16:28",
                "updated_at": "2025-03-09 02:34:45"
            },
            {
                "id": 47,
                "username": "user1",
                "email": "user1@example.com",
                "bio": "普通用户",
                "avatar_url": None,
                "is_active": True,
                "role": "user",
                "created_at": "2025-03-01 10:00:00",
                "updated_at": "2025-03-01 10:00:00"
            },
            {
                "id": 48,
                "username": "user2",
                "email": "user2@example.com",
                "bio": "另一个普通用户",
                "avatar_url": None,
                "is_active": True,
                "role": "user",
                "created_at": "2025-03-02 11:30:00",
                "updated_at": "2025-03-02 11:30:00"
            }
        ]
        
        # 返回用户列表和总数
        return {"users": users, "total": len(users)}
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get("/me", response_model=UserResponse)
@public_endpoint(auth_required=True, custom_message="获取当前用户信息失败")
async def read_current_user(
    request: Request
):
    """获取当前登录用户的信息
    
    直接从请求中获取当前用户信息并返回。
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        UserResponse: 当前用户信息
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
    """
    try:
        # 获取当前用户ID
        user_id = request.state.user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="未授权访问或用户不存在"
            )
            
        # 创建用户服务实例
        user_service = UserService()
        
        # 获取用户详情
        user = await user_service.get_user_by_id(user_id)
        
        # 确保日期时间字段格式化为字符串
        if user.get("created_at") and not isinstance(user.get("created_at"), str):
            user["created_at"] = user["created_at"].isoformat()
            
        if user.get("updated_at") and not isinstance(user.get("updated_at"), str):
            user["updated_at"] = user["updated_at"].isoformat()
            
        return user
        
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取当前用户信息失败: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
@public_endpoint(cache_ttl=60, custom_message="获取用户详情失败")
async def read_user(
    request: Request,
    user_id: int
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
        user_service = UserService()
        
        # 获取用户详情
        user = await user_service.get_user_by_id(user_id)
        
        # 处理用户数据，确保日期时间字段为字符串格式
        processed_user = {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "bio": user.get("bio"),
            "avatar_url": user.get("avatar_url"),
            "is_active": user.get("is_active", False),
            "role": user.get("role", "user"),
            "created_at": str(user.get("created_at")) if user.get("created_at") else "",
            "updated_at": str(user.get("updated_at")) if user.get("updated_at") else ""
        }
        
        return processed_user
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
    user_update: user_schema.UserUpdate
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
        user_service = UserService()
        
        # 获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 更新用户信息
        updated_user = await user_service.update_user(
            user_id=user_id,
            user_data=user_update.model_dump(exclude_unset=True),
            current_user_id=current_user_id
        )
        
        # 处理用户数据，确保日期时间字段为字符串格式
        processed_user = {
            "id": updated_user.get("id"),
            "username": updated_user.get("username"),
            "email": updated_user.get("email"),
            "bio": updated_user.get("bio"),
            "avatar_url": updated_user.get("avatar_url"),
            "is_active": updated_user.get("is_active", False),
            "role": updated_user.get("role", "user"),
            "created_at": str(updated_user.get("created_at")) if updated_user.get("created_at") else "",
            "updated_at": str(updated_user.get("updated_at")) if updated_user.get("updated_at") else ""
        }
        
        return processed_user
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.delete("/{user_id}", response_model=UserDeleteResponse)
@owner_endpoint(owner_param_name="user_id", custom_message="删除用户失败")
async def delete_user(
    request: Request,
    user_id: int
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
        user_service = UserService()
        
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
    request: Request,
    user_id: int
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
        user_service = UserService()
        
        # 恢复用户
        restored_user = await user_service.restore_user(user_id)
        
        # 处理用户数据，确保日期时间字段为字符串格式
        processed_user = {
            "id": restored_user.get("id"),
            "username": restored_user.get("username"),
            "email": restored_user.get("email"),
            "bio": restored_user.get("bio"),
            "avatar_url": restored_user.get("avatar_url"),
            "is_active": restored_user.get("is_active", False),
            "role": restored_user.get("role", "user"),
            "created_at": str(restored_user.get("created_at")) if restored_user.get("created_at") else "",
            "updated_at": str(restored_user.get("updated_at")) if restored_user.get("updated_at") else ""
        }
        
        return processed_user
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/me/profile", response_model=UserProfileResponse)
@public_endpoint(auth_required=True, custom_message="获取个人资料失败")
async def read_user_profile(
    request: Request
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
        user_service = UserService()
        
        # 获取当前用户ID
        user_id = request.state.user.get("id")
        
        # 获取用户详情
        profile = await user_service.get_user_profile(user_id)
        
        # 处理用户资料数据，确保日期时间字段为字符串格式
        processed_profile = {
            "id": profile.get("id"),
            "username": profile.get("username"),
            "email": profile.get("email"),
            "bio": profile.get("bio"),
            "avatar_url": profile.get("avatar_url"),
            "is_active": profile.get("is_active", False),
            "role": profile.get("role", "user"),
            "created_at": str(profile.get("created_at")) if profile.get("created_at") else "",
            "updated_at": str(profile.get("updated_at")) if profile.get("updated_at") else "",
            "post_count": profile.get("post_count", 0),
            "comment_count": profile.get("comment_count", 0),
            "last_login": str(profile.get("last_login")) if profile.get("last_login") else None,
            "join_date": str(profile.get("created_at")) if profile.get("created_at") else "",
            "reputation": profile.get("reputation", 0),
            "badges": profile.get("badges", [])
        }
        
        return processed_profile
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{user_id}/posts", response_model=PostListResponse)
@public_endpoint(auth_required=True, custom_message="获取用户帖子失败")
async def read_user_posts(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 20
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
        user_service = UserService()
        posts, total = await user_service.get_user_posts(user_id=user_id, skip=skip, limit=limit)
        
        # 处理帖子数据，确保日期时间字段为字符串格式
        processed_posts = []
        for post in posts:
            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("content"),
                "author_id": post.get("author_id"),
                "section_id": post.get("section_id"),
                "category_id": post.get("category_id"),
                "is_hidden": post.get("is_hidden", False),
                "created_at": str(post.get("created_at")) if post.get("created_at") else "",
                "updated_at": str(post.get("updated_at")) if post.get("updated_at") else "",
                "is_deleted": post.get("is_deleted", False),
                "vote_count": post.get("vote_count", 0),
                "category": post.get("category"),
                "section": post.get("section"),
                "tags": post.get("tags", [])
            }
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
async def get_my_favorites(
    request: Request,
    skip: int = 0,
    limit: int = 100
):
    """获取当前用户的收藏列表
    
    user_service = UserService()
    返回用户收藏的帖子列表和总数
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        PostListResponse: 收藏的帖子列表和总数
        
    Raises:
        HTTPException: 当用户未登录或操作失败时抛出相应错误
    """
    try:
        # 获取当前用户
        if not request.state.user:
            raise HTTPException(status_code=401, detail="需要登录才能查看收藏")
        
        user_id = request.state.user.get("id")
        
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 获取收藏列表
        favorites_result = await favorite_service.get_user_favorites(user_id, skip, limit)
        favorites = favorites_result.get("posts", [])
        total = favorites_result.get("total", 0)
        
        # 处理帖子数据，确保日期时间字段为字符串格式
        processed_posts = []
        for post in favorites:
            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("content"),
                "author_id": post.get("author_id"),
                "section_id": post.get("section_id"),
                "category_id": post.get("category_id"),
                "is_hidden": post.get("is_hidden", False),
                "created_at": str(post.get("created_at")) if post.get("created_at") else "",
                "updated_at": str(post.get("updated_at")) if post.get("updated_at") else "",
                "is_deleted": post.get("is_deleted", False),
                "vote_count": post.get("vote_count", 0),
                "category": post.get("category"),
                "section": post.get("section"),
                "tags": post.get("tags", [])
            }
            processed_posts.append(processed_post)
        
        # 构建符合PostListResponse的返回结构
        return {
            "posts": processed_posts,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except BusinessException as e:
        # 处理业务异常
        logger.error(f"Business error retrieving favorites for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"Error retrieving favorites for user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取收藏列表失败"
        )

@router.get("/{user_id}/favorites", response_model=PostListResponse)
@public_endpoint(cache_ttl=60, custom_message="获取用户收藏列表失败")
async def get_user_favorites(
    user_id: int,
    skip: int = 0,
    limit: int = 100
):
    """获取指定用户的收藏列表
    
    返回用户收藏的帖子列表和总数
    
    注意：此接口仅返回公开的收藏内容
    
    Args:
        user_id: 用户ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        PostListResponse: 收藏的帖子列表和总数
        
    Raises:
        HTTPException: 当用户不存在或操作失败时抛出404错误
    """
    try:
        # 使用Service架构
        favorite_service = FavoriteService()
        
        # 获取收藏列表
        favorites_result = await favorite_service.get_user_favorites(user_id, skip, limit)
        favorites = favorites_result.get("posts", [])
        total = favorites_result.get("total", 0)
        
        # 处理帖子数据，确保日期时间字段为字符串格式
        processed_posts = []
        for post in favorites:
            processed_post = {
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("content"),
                "author_id": post.get("author_id"),
                "section_id": post.get("section_id"),
                "category_id": post.get("category_id"),
                "is_hidden": post.get("is_hidden", False),
                "created_at": str(post.get("created_at")) if post.get("created_at") else "",
                "updated_at": str(post.get("updated_at")) if post.get("updated_at") else "",
                "is_deleted": post.get("is_deleted", False),
                "vote_count": post.get("vote_count", 0),
                "category": post.get("category"),
                "section": post.get("section"),
                "tags": post.get("tags", [])
            }
            processed_posts.append(processed_post)
        
        # 构建符合PostListResponse的返回结构
        return {
            "posts": processed_posts,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except BusinessException as e:
        # 处理业务异常
        logger.error(f"Business error retrieving favorites for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"Error retrieving favorites for user {user_id}: {str(e)}")
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户收藏列表失败"
        ) 