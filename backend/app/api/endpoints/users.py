from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.database import get_db
from ...schemas import user as user_schema
from ...schemas import post as post_schema
from ...schemas import auth as auth_schema
from ...crud import user as user_crud
from ...crud import favorite as favorite_crud
from ...dependencies import get_current_user, require_user, require_admin
from ...core.endpoint_utils import (
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

router = APIRouter()

@router.post("/", response_model=user_schema.User)
@handle_exceptions(SQLAlchemyError, status_code=500, message="创建用户失败", include_details=True)
@rate_limit(limit=20, window=3600)  # 每小时最多创建20个用户
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def create_user(
    request: Request,
    user: user_schema.UserCreate,
    db: Session = Depends(get_db)
):
    """创建新用户
    
    注册一个新用户账号。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 速率限制：每小时最多创建20个用户
    3. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        user: 用户创建模型，包含用户信息
        db: 数据库会话实例
        
    Returns:
        User: 创建成功的用户信息
        
    Raises:
        HTTPException: 当用户名或邮箱已存在时抛出400错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    db_user = user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[user_schema.User])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取用户列表失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sort: Optional[str] = None,
    order: Optional[str] = "asc",
    current_user: auth_schema.TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表
    
    获取系统中所有用户的列表，支持分页、排序和过滤。
    需要登录才能访问。
    
    Args:
        request: FastAPI请求对象
        skip: 跳过的记录数
        limit: 返回的最大记录数
        sort: 排序字段
        order: 排序方向，asc或desc
        current_user: 当前登录用户
        db: 数据库会话实例
        
    Returns:
        List[User]: 用户列表
        
    Raises:
        HTTPException: 当权限不足或令牌无效时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    print("\n[DEBUG] 收到users接口请求")
    print(f"[DEBUG] 当前用户: {current_user.username}, 角色: {current_user.role}")
    
    # 输出所有请求头，以便调试
    if request:
        print("[DEBUG] 请求头信息:")
        for header_name, header_value in request.headers.items():
            print(f"  {header_name}: {header_value}")
    
    users = user_crud.get_users(db, skip=skip, limit=limit, sort=sort, order=order)
    return users

@router.get("/{user_id}", response_model=user_schema.User)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取用户详情失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=300, include_query_params=True, include_user_id=True)
async def read_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户详情
    
    获取指定用户的详细信息。
    用户可以查看自己的信息，管理员可以查看任何用户的信息。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        db: 数据库会话实例
        
    Returns:
        User: 用户详细信息
        
    Raises:
        HTTPException: 当用户不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 检查权限
    user_role = request.state.user.get("role", "user")
    current_user_id = request.state.user.get("id")
    
    # 只允许本人或管理员查看详情
    if user_role not in ["admin", "super_admin", "moderator"] and str(current_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户信息"
        )
        
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

@router.put("/{user_id}", response_model=user_schema.User)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新用户信息失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@rate_limit(limit=10, window=3600)  # 每小时最多更新10次
async def update_user(
    request: Request,
    user_id: int,
    user: user_schema.UserUpdate,
    db: Session = Depends(get_db)
):
    """更新用户信息
    
    更新指定用户的信息。
    用户可以更新自己的信息，管理员可以更新任何用户的信息。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        user: 用户更新模型，包含要更新的信息
        db: 数据库会话实例
        
    Returns:
        User: 更新后的用户信息
        
    Raises:
        HTTPException: 当用户不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 检查权限
    user_role = request.state.user.get("role", "user")
    current_user_id = request.state.user.get("id")
    
    # 只允许本人或管理员更新信息
    if user_role not in ["admin", "super_admin"] and str(current_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限修改此用户信息"
        )
    
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
        
    # 如果修改用户名，检查是否已存在
    if user.username and user.username != db_user.username:
        existing_user = user_crud.get_user_by_username(db, username=user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
    
    # 如果修改邮箱，检查是否已存在
    if user.email and user.email != db_user.email:
        existing_user = user_crud.get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
            
    return user_crud.update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除用户失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除用户
    
    软删除指定的用户。
    用户可以删除自己的账户，管理员可以删除任何用户。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        db: 数据库会话实例
        
    Returns:
        JSONResponse: 删除操作结果
        
    Raises:
        HTTPException: 当用户不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 检查权限
    user_role = request.state.user.get("role", "user")
    current_user_id = request.state.user.get("id")
    
    # 超级管理员不能被删除
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
        
    if db_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员账户不能被删除"
        )
    
    # 只允许本人或管理员删除
    if user_role not in ["admin", "super_admin"] and str(current_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此用户"
        )
        
    user_crud.delete_user(db=db, user_id=user_id)
    return JSONResponse(content={"message": "用户已删除", "id": user_id})

@router.post("/{user_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复用户失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def restore_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的用户
    
    恢复指定的已删除用户。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        user_id: 要恢复的用户ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当用户不存在、未被删除或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = user_crud.restore_user(db=db, user_id=user_id)
    return result

@router.get("/me/profile", response_model=user_schema.UserProfile)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取个人资料失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=60, include_user_id=True)
async def read_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前用户的个人资料
    
    获取当前登录用户的详细个人资料信息。
    
    Args:
        request: FastAPI请求对象
        db: 数据库会话实例
        
    Returns:
        UserProfile: 用户个人资料
        
    Raises:
        HTTPException: 当用户不存在或令牌无效时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    user_id = request.state.user.get("id")
    user = user_crud.get_user_profile(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

@router.get("/{user_id}/posts", response_model=List[post_schema.Post])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取用户帖子失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=60, include_query_params=True)
async def read_user_posts(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取用户发布的帖子
    
    获取指定用户发布的所有帖子，支持分页。
    
    Args:
        request: FastAPI请求对象
        user_id: 用户ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认20
        db: 数据库会话实例
        
    Returns:
        List[Post]: 用户的帖子列表
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 检查用户是否存在
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
        
    posts = user_crud.get_user_posts(db, user_id=user_id, skip=skip, limit=limit)
    return posts

@router.get("/me/favorites", response_model=post_schema.PostFavoritesList)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取收藏列表失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def get_my_favorites(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取当前用户的收藏列表
    
    返回用户收藏的帖子列表和总数
    """
    # 获取当前用户
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能查看收藏")
    
    # 获取收藏列表
    result = favorite_crud.get_user_favorites(db, current_user.id, skip, limit)
    return result

@router.get("/{user_id}/favorites", response_model=post_schema.PostFavoritesList)
@public_endpoint(cache_ttl=60, custom_message="获取用户收藏列表失败")
async def get_user_favorites(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取指定用户的收藏列表
    
    返回用户收藏的帖子列表和总数
    
    注意：此接口仅返回公开的收藏内容
    """
    # 检查用户是否存在
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取收藏列表
    result = favorite_crud.get_user_favorites(db, user_id, skip, limit)
    return result 