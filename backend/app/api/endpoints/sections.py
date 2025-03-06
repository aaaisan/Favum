from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import logging
from ...core.permissions import check_admin, PermissionChecker, Role
from ...db.database import get_db
from ...schemas.section import SectionCreate, Section, SectionUpdate
from ...schemas import post as post_schema
from ...crud import section as section_crud
from ...core.auth import get_current_active_user
from ...db.query import BoardQuery
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token, require_roles
from ...core.decorators.performance import cache, rate_limit
from ...core.decorators.logging import log_execution_time

router = APIRouter()
permissions = PermissionChecker()

@router.post("/", response_model=Section)
@handle_exceptions(SQLAlchemyError, status_code=500, message="创建版块失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def create_section(
    request: Request,
    section: SectionCreate,
    db: Session = Depends(get_db)
):
    """创建新版块
    
    创建一个新的论坛版块。
    仅管理员可以执行此操作。
    
    Args:
        section: 版块创建模型，包含版块信息
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        Section: 创建成功的版块信息
        
    Raises:
        HTTPException: 当权限不足时抛出403错误
    """
    return section_crud.create_section(db=db, section=section)

@router.get("/", response_model=List[Section])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取版块列表失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=300, include_query_params=True)
async def read_sections(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取版块列表
    
    获取所有论坛版块的列表，支持分页。
    此接口对所有用户开放。
    
    Args:
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        db: 数据库会话实例
        
    Returns:
        List[Section]: 版块列表
    """
    return section_crud.get_sections(db, skip=skip, limit=limit)

@router.put("/{section_id}", response_model=Section)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新版块失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def update_section(
    request: Request,
    section_id: int,
    section: SectionUpdate,
    db: Session = Depends(get_db)
):
    """更新版块信息
    
    更新指定版块的信息。
    仅管理员可以执行此操作。
    
    Args:
        section_id: 版块ID
        section: 版块更新模型，包含要更新的信息
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        Section: 更新后的版块信息
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误，当权限不足时抛出403错误
    """
    db_section = section_crud.get_section(db, section_id=section_id)
    if db_section is None:
        raise HTTPException(status_code=404, detail="版块不存在")
    return section_crud.update_section(db=db, section_id=section_id, section=section)

@router.post("/{section_id}/moderators/{user_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="添加版主失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def add_moderator(
    request: Request,
    section_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """添加版主
    
    为指定版块添加一个版主。
    仅管理员可以执行此操作。
    
    Args:
        section_id: 版块ID
        user_id: 要添加为版主的用户ID
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        dict: 操作结果信息
        
    Raises:
        HTTPException: 当版块或用户不存在时抛出404错误，当权限不足时抛出403错误
    """
    return section_crud.add_moderator(db=db, section_id=section_id, user_id=user_id)

@router.delete("/{section_id}/moderators/{user_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="移除版主失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以移除版主
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def remove_moderator(
    request: Request,
    section_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """移除版主"""
    result = section_crud.remove_moderator(db=db, section_id=section_id, user_id=user_id)
    return result

@router.get("/{section_id}/posts", response_model=List[post_schema.Post])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取版块帖子失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@cache(expire=300, include_query_params=True)  # 缓存5分钟
async def get_section_posts(
    request: Request,
    section_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取版块的所有帖子
    
    获取指定版块下的所有帖子，支持分页。
    
    Args:
        section_id: 版块ID
        skip: 跳过的记录数，用于分页
        limit: 每页记录数，默认20条
        db: 数据库会话实例
        
    Returns:
        List[Post]: 帖子列表
        
    Raises:
        HTTPException: 当版块不存在时抛出404错误
    """
    # 首先检查版块是否存在
    section = section_crud.get_section(db, section_id)
    if not section:
        raise HTTPException(
            status_code=404,
            detail="版块不存在"
        )
    
    # 使用BoardQuery获取版块帖子
    posts = BoardQuery.get_board_posts(
        db=db,
        board_id=section_id,
        skip=skip,
        limit=limit,
        include_user=True
    )
    
    return posts

@router.delete("/{section_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除版块失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以删除
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def delete_section(
    request: Request,
    section_id: int,
    db: Session = Depends(get_db)
):
    """删除版块"""
    result = section_crud.delete_section(db=db, section_id=section_id)
    return result

@router.post("/{section_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复版块失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以恢复
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def restore_section(
    request: Request,
    section_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的版块
    
    恢复指定的已删除版块。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复版块
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        section_id: 要恢复的版块ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当版块不存在、未被删除或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = section_crud.restore_section(db=db, section_id=section_id)
    return result

@router.post("/{section_id}/moderators/{user_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复版主失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以恢复版主
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def restore_moderator(
    request: Request,
    section_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的版主
    
    恢复指定的已删除版主。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复版主
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        section_id: 版块ID
        user_id: 要恢复的用户ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当版块不存在、用户不存在、记录不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = section_crud.restore_moderator(db=db, section_id=section_id, user_id=user_id)
    return result 