from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from ...core.permissions import Permission, Role
from ...db.database import get_db
from ...schemas import post as post_schema
from ...crud import post as post_crud
from ...core.auth import get_current_active_user
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token, require_permissions, require_roles, owner_required
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time
from ...core.endpoint_utils import (
    admin_endpoint,
    moderator_endpoint,
    public_endpoint,
    owner_endpoint
)
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from ...db.models import SectionModerator
import logging
from ...dependencies import get_current_user, require_user, check_post_ownership
from ...crud import favorite as favorite_crud

router = APIRouter()

def get_post_owner(post_id: int, db: Session = Depends(get_db)) -> int:
    """获取帖子作者ID
    
    用于权限验证，获取指定帖子的作者ID。
    
    Args:
        post_id: 帖子ID
        db: 数据库会话实例
        
    Returns:
        int: 帖子作者的用户ID
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    post = post_crud.get_post(db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post.author_id

@router.post("/", response_model=post_schema.Post)
@public_endpoint(rate_limit_count=10, auth_required=True, custom_message="创建帖子失败")
async def create_post(
    request: Request,
    post: post_schema.PostCreate,
    db: Session = Depends(get_db)
):
    """创建新帖子"""
    # 不从令牌中获取用户ID，直接使用提供的author_id
    return post_crud.create_post(db=db, post=post)

@router.post("/test", response_model=post_schema.Post)
async def test_create_post(
    post: post_schema.PostCreate,
    db: Session = Depends(get_db)
):
    """测试创建帖子
    
    用于测试的简化版创建帖子API。
    """
    return post_crud.create_post(db=db, post=post)

@router.get("/", response_model=post_schema.PostList)
@public_endpoint(cache_ttl=60, custom_message="获取帖子列表失败")
async def read_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取帖子列表
    
    获取系统中的帖子列表，支持分页。
    此API端点允许游客访问。
    
    Args:
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        db: 数据库会话实例
        
    Returns:
        PostList: 包含帖子列表和总数的响应
        
    Raises:
        HTTPException: 当数据库操作失败时抛出500错误
    """
    try:
        # 记录请求信息
        logger = logging.getLogger("posts_api")
        logger.error(f"获取帖子列表: skip={skip}, limit={limit}")
        
        # 获取帖子列表
        posts = post_crud.get_posts(db, skip=skip, limit=limit)
        logger.error(f"获取到 {len(posts)} 条帖子")
        
        # 获取帖子总数
        total = post_crud.get_posts_count(db)
        logger.error(f"帖子总数: {total}")
        
        # 构建响应
        response = {
            "posts": posts,
            "total": total,
            "page_size": limit
        }
        
        # 记录响应信息
        logger.error(f"响应数据: posts={len(posts)}, total={total}, page_size={limit}")
        
        return response
    except Exception as e:
        logger = logging.getLogger("posts_api")
        logger.error(f"获取帖子列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取帖子列表失败: {str(e)}")

@router.get("/{post_id}", response_model=post_schema.Post)
@public_endpoint(cache_ttl=60, custom_message="获取帖子详情失败")
async def read_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """获取帖子详情
    
    获取指定ID的帖子详细信息。
    
    Args:
        post_id: 帖子ID
        db: 数据库会话实例
        
    Returns:
        Post: 帖子详细信息
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    post = post_crud.get_post(db, post_id=post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post

@router.put("/{post_id}", response_model=post_schema.Post)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新帖子失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def update_post(
    request: Request,
    post_id: int,
    post: post_schema.PostUpdate,
    db: Session = Depends(get_db)
):
    """更新帖子
    
    更新指定ID的帖子信息，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        post: 更新的帖子数据
        db: 数据库会话实例
        
    Returns:
        Post: 更新后的帖子信息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    db_post = post_crud.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查权限
    user_role = request.state.user.get("role", "user")
    user_id = request.state.user.get("id")
    
    # 如果是管理员或版主，直接允许访问
    if user_role not in ["admin", "super_admin", "moderator"]:
        # 检查是否为资源所有者
        owner_id = get_post_owner(post_id=post_id, db=db)
        if str(owner_id) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="没有权限访问此资源"
            )
    
    return post_crud.update_post(db=db, post_id=post_id, post=post)

@router.delete("/{post_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除帖子失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def delete_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """删除帖子
    
    软删除指定的帖子，仅允许帖子作者、版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        db: 数据库会话实例
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    # 检查权限
    user_role = request.state.user.get("role", "user")
    user_id = request.state.user.get("id")
    
    # 如果是管理员或版主，直接允许访问
    if user_role not in ["admin", "super_admin", "moderator"]:
        # 检查是否为资源所有者
        owner_id = get_post_owner(post_id=post_id, db=db)
        if str(owner_id) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="没有权限访问此资源"
            )
    
    return post_crud.delete_post(db=db, post_id=post_id)

@router.post("/{post_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复帖子失败", include_details=True)
@validate_token
@require_roles([Role.MODERATOR, Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def restore_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的帖子
    
    恢复指定的已删除帖子，仅允许版主和管理员操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        db: 数据库会话实例
        
    Returns:
        dict: 操作结果消息
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
    """
    return post_crud.restore_post(db=db, post_id=post_id)

@router.patch("/{post_id}/visibility")
@handle_exceptions(SQLAlchemyError, status_code=500, message="更改帖子可见性失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def toggle_post_visibility(
    request: Request,
    post_id: int,
    visibility: dict,
    db: Session = Depends(get_db)
):
    """切换帖子可见性
    
    隐藏或显示指定的帖子。
    权限规则：
    1. 管理员可以隐藏/显示任何帖子
    2. 版主可以隐藏/显示其管理的版块中的帖子
    3. 普通用户只能隐藏/显示自己的帖子
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        visibility: 包含可见性设置的字典，例如 {"hidden": true}
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息和更新后的帖子状态的响应
        
    Raises:
        HTTPException: 当帖子不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 检查帖子是否存在
    db_post = post_crud.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 从token中获取用户ID和角色
    user_data = request.state.user
    user_id = user_data.get("id")
    user_role = user_data.get("role", "user")
    
    # 检查权限
    if user_role in ["admin", "super_admin"]:
        # 管理员可以隐藏任何帖子
        pass
    elif user_role == "moderator":
        # 版主需要检查是否管理该版块
        is_moderator = db.query(SectionModerator).filter(
            SectionModerator.section_id == db_post.section_id,
            SectionModerator.user_id == user_id
        ).first()
        if not is_moderator:
            raise HTTPException(status_code=403, detail="您不是该版块的版主，无权隐藏此帖子")
    else:
        # 普通用户只能隐藏自己的帖子
        if db_post.author_id != user_id:
            raise HTTPException(status_code=403, detail="您只能隐藏自己的帖子")
    
    # 更新帖子可见性
    is_hidden = visibility.get("hidden", not db_post.is_hidden)  # 如果未提供，则切换当前状态
    updated_post = post_crud.toggle_post_hidden(db, post_id, is_hidden)
    
    status_text = "隐藏" if updated_post.is_hidden else "显示"
    return {
        "detail": f"帖子已{status_text}",
        "post_id": post_id,
        "is_hidden": updated_post.is_hidden
    }

@router.post("/{post_id}/vote", response_model=post_schema.VoteResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="点赞操作失败")
async def vote_post(
    request: Request,
    post_id: int,
    vote: post_schema.PostVoteCreate,
    db: Session = Depends(get_db)
):
    """对帖子进行点赞或反对
    
    用户可以对帖子进行点赞（赞数+1）或反对（赞数-1）。
    如果用户已经点赞/反对过该帖子，则再次点击相同操作会取消。
    如果用户已经点赞后点击反对，会取消点赞并添加反对，反之亦然。
    
    需要登录才能进行点赞或反对操作。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        vote: 点赞操作信息，包含点赞类型
        db: 数据库会话实例
        
    Returns:
        dict: 包含操作结果、更新后的点赞数和消息
        
    Raises:
        HTTPException: 当用户未登录时抛出401错误，当帖子不存在时抛出404错误，当操作失败时抛出400错误
    """
    # 检查用户是否已登录
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="需要登录才能点赞或反对")
    
    # 获取当前用户ID
    user_id = request.state.user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="需要登录才能点赞或反对")
    
    # 调用CRUD函数进行点赞操作
    return post_crud.vote_post(db, post_id, user_id, vote.vote_type)

@router.get("/{post_id}/votes", response_model=int)
@public_endpoint(cache_ttl=10, custom_message="获取点赞数失败")
async def get_post_votes(
    post_id: int,
    db: Session = Depends(get_db)
):
    """获取帖子的点赞数
    
    Args:
        post_id: 帖子ID
        db: 数据库会话实例
        
    Returns:
        int: 帖子的点赞数
        
    Raises:
        HTTPException: 当帖子不存在时抛出404错误
    """
    return post_crud.get_post_votes(db, post_id)

@router.post("/{post_id}/favorite", response_model=post_schema.FavoriteResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="收藏操作失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def favorite_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """收藏帖子
    
    将指定帖子添加到当前用户的收藏列表中
    """
    # 获取当前用户ID
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能收藏帖子")
    
    # 添加收藏
    result = favorite_crud.add_favorite(db, post_id, current_user.id)
    return result

@router.delete("/{post_id}/favorite", response_model=post_schema.FavoriteResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="取消收藏失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def unfavorite_post(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """取消收藏帖子
    
    从当前用户的收藏列表中移除指定帖子
    """
    # 获取当前用户ID
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能操作收藏")
    
    # 移除收藏
    result = favorite_crud.remove_favorite(db, post_id, current_user.id)
    return result

@router.get("/{post_id}/favorite/status", response_model=bool)
@public_endpoint(cache_ttl=10, custom_message="获取收藏状态失败")
async def check_favorite_status(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db)
):
    """检查当前用户是否已收藏指定帖子
    
    返回布尔值，表示当前用户是否已收藏该帖子
    """
    # 获取当前用户ID
    current_user = await get_current_user(request)
    if not current_user:
        return False
    
    # 检查收藏状态
    status = favorite_crud.is_post_favorited(db, post_id, current_user.id)
    return status
