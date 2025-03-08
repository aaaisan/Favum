from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from ...schemas import user as user_schema
from ...schemas import post as post_schema
from ...schemas import auth as auth_schema
from ...services.favorite_service import FavoriteService
from ...dependencies import get_current_user, require_user, require_admin
from ...utils.api_decorators import (
    admin_endpoint,
    moderator_endpoint,
    public_endpoint,
    owner_endpoint
)
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token, require_permissions, require_roles, owner_required
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time
from ...core.enums import Permission, Role
from sqlalchemy.exc import SQLAlchemyError
from ...db.query import UserQuery
import logging
from fastapi.responses import JSONResponse
# 导入新的服务层
from ...services.user_service import UserService  
from ...core.exceptions import BusinessException
from ...db.repositories.user_repository import UserRepository

router = APIRouter()

@router.post("/", response_model=user_schema.User)
@public_endpoint(custom_message="创建用户失败", rate_limit_count=20)
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
        User: 创建成功的用户信息
        
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

@router.get("/", response_model=List[user_schema.User])
@admin_endpoint(custom_message="获取用户列表失败")
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
):
    """获取所有用户列表
    
    user_service = UserService()
    获取所有用户的分页列表，仅管理员可访问。
    支持分页、排序和过滤功能。
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        sort_by: 排序字段，可选
        sort_order: 排序方向，可选，'asc'或'desc'
        
    Returns:
        List[User]: 用户列表
        
    Raises:
        HTTPException: 当用户无权限或令牌无效时抛出相应错误
    """
    try:
        user_service = UserService()
        
        # 获取用户列表
        users = await user_service.get_users(skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order)
        return users
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{user_id}", response_model=user_schema.User)
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
        User: 用户详情
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
    """
    try:
        user_service = UserService()
        
        # 获取用户详情
        user = await user_service.get_user_by_id(user_id)
        return user
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.put("/{user_id}", response_model=user_schema.User)
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
        User: 更新后的用户信息
        
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
        
        return updated_user
        
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{user_id}")
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
        dict: 包含操作结果消息
        
    Raises:
        HTTPException: 当用户不存在、权限不足或令牌无效时抛出相应错误
    """
    try:
        user_service = UserService()
        
        # 获取当前用户ID
        current_user_id = request.state.user.get("id")
        
        # 删除用户
        await user_service.delete_user(user_id=user_id, current_user_id=current_user_id)
        
        return {
            "message": "用户已成功删除"
        }
        
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{user_id}/restore")
@admin_endpoint(custom_message="恢复用户失败")
async def restore_user(
    request: Request,
    user_id: int
):
    """恢复已删除的用户
    
    user_service = UserService()
    将标记为已删除的用户恢复为正常状态。
    此操作仅限管理员执行。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        
    Returns:
        User: 恢复后的用户信息
        
    Raises:
        HTTPException: 当用户不存在、权限不足或令牌无效时抛出相应错误
    """
    try:
        user_service = UserService()
        
        # 恢复用户
        restored_user = await user_service.restore_user(user_id)
        
        return restored_user
        
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/me/profile", response_model=user_schema.UserProfile)
@public_endpoint(auth_required=True, custom_message="获取个人资料失败")
async def read_user_profile(
    request: Request
):
    """获取当前用户的个人资料
    
    user_service = UserService()
    获取当前登录用户的详细个人资料信息。
    结果会被缓存60秒。
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        UserProfile: 用户个人资料
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
    """
    user_id = request.state.user.get("id")
    user_service = UserService()
    user = await user_service.get_user_profile(user_id)
    return user

@router.get("/{user_id}/posts", response_model=post_schema.PostList)
@public_endpoint(auth_required=True, custom_message="获取用户帖子失败")
async def read_user_posts(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取用户发布的帖子
    
    user_service = UserService()
    获取指定用户发布的所有帖子，支持分页。
    结果会被缓存60秒。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认20
        
    Returns:
        PostList: 包含帖子列表的响应对象
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
    """
    user_service = UserService()
    posts, total = await user_service.get_user_posts(user_id=user_id, skip=skip, limit=limit)
    
    return {
        "posts": posts,
        "total": total,
        "page_size": limit
    }

@router.get("/me/favorites", response_model=post_schema.PostFavoritesList)
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
        PostFavoritesList: 收藏的帖子列表和总数
        
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
        result = await favorite_service.get_user_favorites(user_id, skip, limit)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{user_id}/favorites", response_model=post_schema.PostFavoritesList)
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
        PostFavoritesList: 收藏的帖子列表和总数
        
    Raises:
        HTTPException: 当用户不存在或操作失败时抛出相应错误
    """
    try:
        # 使用Service架构
        favorite_service = FavoriteService()
        user_service = UserService()
        
        # 检查用户是否存在
        await user_service.get_user_by_id(user_id)
        
        # 获取收藏列表
        result = await favorite_service.get_user_favorites(user_id, skip, limit)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        ) 