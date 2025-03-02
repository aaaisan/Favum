from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from ...core.permissions import check_admin, Role
from ...db.database import get_db
from ...schemas import category as category_schema
from ...crud import category as category_crud
from ...core.decorators import (
    handle_exceptions, 
    validate_token, 
    require_roles, 
    log_execution_time,
    cache
)
from ...core.endpoint_utils import admin_endpoint, public_endpoint
import logging
from fastapi import status

router = APIRouter()

@router.post("/", response_model=category_schema.Category)
@handle_exceptions(SQLAlchemyError, status_code=500, message="创建分类失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def create_category(
    request: Request,
    category: category_schema.CategoryCreate,
    db: Session = Depends(get_db)
):
    """创建新分类
    
    创建一个新的帖子分类。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category: 分类创建模型，包含分类信息
        db: 数据库会话实例
        
    Returns:
        Category: 创建成功的分类信息
        
    Raises:
        HTTPException: 当权限不足时抛出403错误
    """
    db_category = category_crud.get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分类名称已存在"
        )
    return category_crud.create_category(db=db, category=category)

@router.get("/", response_model=List[category_schema.Category])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取分类列表失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=300, include_query_params=True)
async def read_categories(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取分类列表
    
    获取所有分类的列表，支持分页。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        db: 数据库会话实例
        
    Returns:
        List[Category]: 分类列表
    """
    categories = category_crud.get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/{category_id}", response_model=category_schema.Category)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取分类详情失败", include_details=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
@cache(expire=300, include_query_params=True)
async def read_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取分类详情
    
    获取指定分类的详细信息。
    此接口对所有用户开放。
    
    Args:
        request: FastAPI请求对象
        category_id: 分类ID
        db: 数据库会话实例
        
    Returns:
        Category: 分类详细信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误
    """
    category = category_crud.get_category(db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category

@router.put("/{category_id}", response_model=category_schema.Category)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新分类失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def update_category(
    request: Request,
    category_id: int,
    category: category_schema.CategoryUpdate,
    db: Session = Depends(get_db)
):
    """更新分类信息
    
    更新指定分类的信息。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_id: 分类ID
        category: 分类更新模型，包含要更新的信息
        db: 数据库会话实例
        
    Returns:
        Category: 更新后的分类信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误，当权限不足时抛出403错误
    """
    db_category = category_crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category_crud.update_category(db=db, category_id=category_id, category=category)

@router.delete("/{category_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除分类失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def delete_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db)
):
    """删除分类
    
    删除指定的分类（软删除）。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_id: 要删除的分类ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当分类不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = category_crud.delete_category(db=db, category_id=category_id)
    return result

@router.post("/{category_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复分类失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def restore_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的分类
    
    恢复指定的已删除分类。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有管理员可以恢复分类
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        category_id: 要恢复的分类ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当分类不存在、未被删除或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = category_crud.restore_category(db=db, category_id=category_id)
    return result

@router.post("/reorder")
@handle_exceptions(SQLAlchemyError, status_code=500, message="重新排序分类失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，用时 {execution_time:.3f}秒")
async def reorder_categories(
    request: Request,
    category_ids: List[int],
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """重新排序分类
    
    调整分类的显示顺序。
    支持调整同级分类的顺序，以及移动分类到不同的父分类下。
    仅管理员可以执行此操作。
    
    Args:
        request: FastAPI请求对象
        category_ids: 分类ID列表，按照期望的顺序排列
        parent_id: 父分类ID，如果要移动到顶级分类则为None
        db: 数据库会话实例
        
    Returns:
        dict: 包含更新后的分类顺序信息
        
    Raises:
        HTTPException: 当分类不存在时抛出404错误，当权限不足时抛出403错误
    """
    return category_crud.reorder_categories(db=db, parent_id=parent_id, category_ids=category_ids) 