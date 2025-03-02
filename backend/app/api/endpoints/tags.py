from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from ...core.permissions import check_admin, Role
from ...db.database import get_db
from ...schemas import tag as tag_schema
from ...crud import tag as tag_crud
from ...core.decorators import (
    handle_exceptions, 
    validate_token, 
    require_roles, 
    log_execution_time
)

router = APIRouter()

@router.post("/", response_model=tag_schema.Tag)
async def create_tag(
    tag: tag_schema.TagCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(check_admin)
):
    """创建新标签
    
    创建一个新的帖子标签。
    仅管理员可以执行此操作。
    
    Args:
        tag: 标签创建模型，包含标签信息
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        Tag: 创建成功的标签信息
        
    Raises:
        HTTPException: 当标签已存在时抛出400错误，当权限不足时抛出403错误
    """
    db_tag = tag_crud.get_tag_by_name(db, name=tag.name)
    if db_tag:
        raise HTTPException(status_code=400, detail="标签已存在")
    return tag_crud.create_tag(db=db, tag=tag)

@router.get("/", response_model=List[tag_schema.Tag])
async def read_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取标签列表
    
    获取所有标签的列表，支持分页。
    此接口对所有用户开放。
    
    Args:
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        db: 数据库会话实例
        
    Returns:
        List[Tag]: 标签列表
    """
    return tag_crud.get_tags(db, skip=skip, limit=limit)

@router.get("/popular", response_model=List[tag_schema.Tag])
async def read_popular_tags(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取热门标签
    
    获取使用次数最多的标签列表。
    此接口对所有用户开放。
    
    Args:
        limit: 返回的标签数量，默认10
        db: 数据库会话实例
        
    Returns:
        List[Tag]: 热门标签列表，按使用次数降序排序
    """
    return tag_crud.get_popular_tags(db=db, limit=limit)

@router.get("/recent", response_model=List[tag_schema.Tag])
async def read_recent_tags(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取最近标签
    
    获取最近使用的标签列表。
    此接口对所有用户开放。
    
    Args:
        limit: 返回的标签数量，默认10
        db: 数据库会话实例
        
    Returns:
        List[Tag]: 最近使用的标签列表，按最后使用时间降序排序
    """
    return tag_crud.get_recent_tags(db=db, limit=limit)

@router.get("/{tag_id}", response_model=tag_schema.Tag)
async def read_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """获取标签详情
    
    获取指定标签的详细信息。
    此接口对所有用户开放。
    
    Args:
        tag_id: 标签ID
        db: 数据库会话实例
        
    Returns:
        Tag: 标签详细信息
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误
    """
    db_tag = tag_crud.get_tag(db, tag_id=tag_id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    return db_tag

@router.put("/{tag_id}", response_model=tag_schema.Tag)
async def update_tag(
    tag_id: int,
    tag: tag_schema.TagUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(check_admin)
):
    """更新标签信息
    
    更新指定标签的信息。
    仅管理员可以执行此操作。
    
    Args:
        tag_id: 标签ID
        tag: 标签更新模型，包含要更新的信息
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        Tag: 更新后的标签信息
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误，当权限不足时抛出403错误
    """
    return tag_crud.update_tag(db=db, tag_id=tag_id, tag=tag)

@router.delete("/{tag_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除标签失败")
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以删除
@log_execution_time
async def delete_tag(request: Request, tag_id: int, db: Session = Depends(get_db)):
    """删除标签"""
    result = tag_crud.delete_tag(db=db, tag_id=tag_id)
    return result

@router.post("/{tag_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复标签失败")
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])  # 只有管理员可以恢复
@log_execution_time
async def restore_tag(request: Request, tag_id: int, db: Session = Depends(get_db)):
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
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当标签不存在、未被删除或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = tag_crud.restore_tag(db=db, tag_id=tag_id)
    return result

@router.post("/{tag_id}/update-stats", response_model=tag_schema.Tag)
async def update_tag_statistics(
    tag_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(check_admin)
):
    """更新标签统计信息
    
    更新指定标签的使用统计信息。
    包括：
    1. 使用次数
    2. 最后使用时间
    3. 相关帖子数量
    
    仅管理员可以执行此操作。
    
    Args:
        tag_id: 标签ID
        db: 数据库会话实例
        _: 管理员权限检查依赖
        
    Returns:
        Tag: 更新后的标签信息，包含最新统计数据
        
    Raises:
        HTTPException: 当标签不存在时抛出404错误，当权限不足时抛出403错误
    """
    return tag_crud.update_tag_stats(db=db, tag_id=tag_id) 