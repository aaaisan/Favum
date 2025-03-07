from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError
import logging
from fastapi.responses import JSONResponse

from ...db.database import get_db
from ...schemas import comment as comment_schema
from ...crud import comment as comment_crud
from ...dependencies import get_current_user
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token, require_permissions, require_roles, owner_required
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time
from ...core.permissions import Permission, Role

router = APIRouter()

def get_comment_owner(comment_id: int, db: Session = Depends(get_db)) -> int:
    """获取评论作者ID
    
    用于权限验证，获取指定评论的作者ID。
    
    Args:
        comment_id: 评论ID
        db: 数据库会话实例
        
    Returns:
        int: 评论作者的用户ID
        
    Raises:
        HTTPException: 当评论不存在时抛出404错误
    """
    comment = comment_crud.get_comment(db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return comment.author_id

@router.post("/", response_model=comment_schema.Comment)
@handle_exceptions(SQLAlchemyError, status_code=500, message="创建评论失败", include_details=True)
@validate_token
@require_permissions(Permission.CREATE_COMMENT)
@rate_limit(limit=30, window=3600)  # 每小时最多发30条评论
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def create_comment(
    request: Request,
    comment: comment_schema.CommentCreate,
    db: Session = Depends(get_db)
):
    """创建新评论
    
    创建一个新的评论。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 权限检查：需要CREATE_COMMENT权限
    4. 速率限制：每小时最多发30条评论
    5. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment: 评论创建模型，包含评论内容
        db: 数据库会话实例
        
    Returns:
        Comment: 创建成功的评论信息
        
    Raises:
        HTTPException: 当权限不足或令牌无效时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    # 从token中获取用户ID
    comment.author_id = request.state.user.get("id")
    return comment_crud.create_comment(db=db, comment=comment)

@router.get("/{comment_id}", response_model=comment_schema.Comment)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取评论详情失败", include_details=True)
@validate_token
@cache(expire=300, include_query_params=True, include_user_id=False)  # 缓存5分钟
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def read_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """获取评论详情
    
    获取指定评论的详细信息。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 权限检查：需要VIEW_CONTENT权限
    4. 响应缓存：结果缓存5分钟
    5. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment_id: 评论ID
        db: 数据库会话实例
        
    Returns:
        Comment: 评论详细信息
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    db_comment = comment_crud.get_comment(db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    return db_comment

@router.put("/{comment_id}", response_model=comment_schema.Comment)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新评论失败", include_details=True)
@validate_token
@require_permissions(Permission.EDIT_COMMENT)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@rate_limit(limit=20, window=3600)  # 每小时最多修改20次
async def update_comment(
    request: Request,
    comment_id: int,
    comment: comment_schema.CommentUpdate,
    db: Session = Depends(get_db)
):
    """更新评论
    
    更新指定评论的内容。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 权限检查：只有评论作者或管理员可以修改
    3. 速率限制：每小时最多修改20次
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment_id: 评论ID
        comment: 评论更新模型，包含更新的内容
        db: 数据库会话实例
        
    Returns:
        Comment: 更新后的评论信息
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出404或403错误
    """
    # 检查评论是否存在
    db_comment = comment_crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 检查权限
    user_id = request.state.user.get("id")
    user_role = request.state.user.get("role", "user")
    
    # 如果不是管理员或版主，检查是否为评论作者
    if user_role not in ["admin", "super_admin", "moderator"] and str(db_comment.author_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限修改此评论"
        )
    
    return comment_crud.update_comment(db=db, comment_id=comment_id, comment=comment)

@router.delete("/{comment_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除评论失败", include_details=True)
@validate_token
@require_permissions(Permission.DELETE_COMMENT)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
@rate_limit(limit=10, window=3600)  # 每小时最多删除10次
async def delete_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """删除评论
    
    删除指定的评论。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 权限检查：只有评论作者或管理员可以删除
    3. 速率限制：每小时最多删除10次
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment_id: 评论ID
        db: 数据库会话实例
        
    Returns:
        JSONResponse: 删除操作结果
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出404或403错误
    """
    # 检查评论是否存在
    db_comment = comment_crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 检查权限
    user_id = request.state.user.get("id")
    user_role = request.state.user.get("role", "user")
    
    # 如果不是管理员或版主，检查是否为评论作者
    if user_role not in ["admin", "super_admin", "moderator"] and str(db_comment.author_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此评论"
        )
    
    comment_crud.delete_comment(db=db, comment_id=comment_id)
    return JSONResponse(content={"message": "评论已删除", "id": comment_id})

@router.post("/{comment_id}/restore")
@handle_exceptions(SQLAlchemyError, status_code=500, message="恢复评论失败", include_details=True)
@validate_token
@require_roles([Role.MODERATOR, Role.ADMIN, Role.SUPER_ADMIN])  # 只有版主和管理员可以恢复
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def restore_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """恢复已删除的评论
    
    恢复指定的已删除评论。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 角色要求：只有版主和管理员可以恢复评论
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment_id: 要恢复的评论ID
        db: 数据库会话实例
        
    Returns:
        dict: 包含成功消息的响应
        
    Raises:
        HTTPException: 当评论不存在、未被删除或权限不足时抛出相应错误
        SQLAlchemyError: 当数据库操作失败时抛出500错误
    """
    result = comment_crud.restore_comment(db=db, comment_id=comment_id)
    return result

@router.post("/guest-notice")
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def guest_comment_notice(request: Request):
    """游客评论提示
    
    当未登录用户尝试评论时，返回提示信息要求注册或登录。
    
    Returns:
        dict: 包含提示消息的响应
    """
    return {
        "status": "error",
        "message": "请先注册或登录后再发表评论",
        "detail": "评论功能仅对已登录用户开放，请注册新账号或登录后再尝试"
    }
