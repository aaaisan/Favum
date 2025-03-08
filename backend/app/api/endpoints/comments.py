from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException, status, Request
from typing import List
from typing import List, Optional
from fastapi.responses import JSONResponse

from ...schemas import comment as comment_schema
from ...services.comment_service import CommentService
from ...core.exceptions import BusinessException
from ...core.decorators import public_endpoint, admin_endpoint, owner_endpoint

# 导入响应模型

from ..responses import (
    CommentResponse,
    CommentListResponse,
    CommentDeleteResponse
)

router = APIRouter()

async def get_comment_owner(comment_id: int) -> int:
    """获取评论作者ID
    
    用于权限验证，获取指定评论的作者ID。
    
    Args:
        comment_id: 评论ID
        
    Returns:
        int: 评论作者的用户ID
        
    Raises:
        HTTPException: 当评论不存在时抛出404错误
    """
    # 使用Service架构
    comment_service = CommentService()
    
    try:
        # 直接调用异步方法
        comment = await comment_service.get_comment_detail(comment_id)
        return comment.get("author_id")
    except BusinessException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/", response_model=CommentResponse)
@public_endpoint(rate_limit_count=30, auth_required=True, custom_message="创建评论失败")
async def create_comment(
    request: Request,
    comment: comment_schema.CommentCreate
):
    """创建新评论
    
    创建一个新的评论。
    包含以下特性：
    1. 异常处理：自动处理数据库异常和业务异常
    2. 速率限制：每小时最多创建30条评论
    3. 权限检查：需要CREATE_COMMENT权限
    
    Args:
        request: FastAPI请求对象
        comment: 评论创建模型，包含评论内容
        
    Returns:
        CommentResponse: 创建成功的评论信息
        
    Raises:
        HTTPException: 当用户未登录或评论内容不符合要求时抛出相应错误
    """
    # 使用 Service 架构替代直接 CRUD 操作
    comment_service = CommentService()
    
    # 从token中获取用户ID
    user_id = request.state.user.get("id")
    
    # 准备评论数据
    comment_data = comment.model_dump()
    comment_data["author_id"] = user_id
    
    try:
        # 创建评论
        result = await comment_service.create_comment(comment_data)
        return result
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.get("/{comment_id}", response_model=CommentResponse)
@public_endpoint(cache_ttl=300, auth_required=True, custom_message="获取评论详情失败")
async def read_comment(
    request: Request,
    comment_id: int
):
    """获取评论详情
    
    获取指定评论的详细信息。
    包含以下特性：
    1. 异常处理：自动处理数据库异常
    2. 令牌验证：需要有效的访问令牌
    3. 响应缓存：结果缓存5分钟
    4. 执行时间日志：记录API执行时间
    
    Args:
        request: FastAPI请求对象
        comment_id: 评论ID
        
    Returns:
        CommentResponse: 评论详细信息
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出相应错误
        BusinessException: 当业务规则验证失败时抛出业务异常
    """
    # 使用 Service 架构替代直接 CRUD 操作
    comment_service = CommentService()
    
    try:
        # 获取评论详情
        comment = await comment_service.get_comment_detail(comment_id)
        return comment
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.put("/{comment_id}", response_model=CommentResponse)
@public_endpoint(rate_limit_count=20, auth_required=True, custom_message="更新评论失败")
async def update_comment(
    request: Request,
    comment_id: int,
    comment: comment_schema.CommentUpdate
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
        
    Returns:
        CommentResponse: 更新后的评论信息
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出404或403错误
        BusinessException: 当业务规则验证失败时抛出业务异常
    """
    # 使用 Service 架构替代直接 CRUD 操作
    comment_service = CommentService()
    
    # 从token中获取用户ID
    user_id = request.state.user.get("id")
    
    try:
        # 更新评论
        updated_comment = await comment_service.update_comment(
            comment_id=comment_id,
            user_id=user_id,
            data=comment.model_dump()
        )
        return updated_comment
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.delete("/{comment_id}", response_model=CommentDeleteResponse)
@public_endpoint(rate_limit_count=10, auth_required=True, custom_message="删除评论失败")
async def delete_comment(
    request: Request,
    comment_id: int
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
        
    Returns:
        CommentDeleteResponse: 删除操作结果
        
    Raises:
        HTTPException: 当评论不存在或权限不足时抛出404或403错误
        BusinessException: 当业务规则验证失败时抛出业务异常
    """
    # 使用 Service 架构替代直接 CRUD 操作
    comment_service = CommentService()
    
    # 从token中获取用户ID和角色
    user_id = request.state.user.get("id")
    user_role = request.state.user.get("role", "user")
    is_admin = user_role in ["admin", "super_admin", "moderator"]
    
    try:
        # 删除评论
        await comment_service.delete_comment(
            comment_id=comment_id,
            user_id=user_id,
            is_admin=is_admin
        )
        
        # 构建符合CommentDeleteResponse的返回结构
        return {
            "id": comment_id,
            "message": "评论已成功删除"
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/{comment_id}/restore", response_model=CommentResponse)
@admin_endpoint(custom_message="恢复评论失败")
async def restore_comment(
    request: Request,
    comment_id: int
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
        
    Returns:
        CommentResponse: 包含成功消息的响应
        
    Raises:
        HTTPException: 当评论不存在或未被删除时抛出相应错误
        BusinessException: 当业务规则验证失败时抛出业务异常
    """
    # 使用 Service 架构替代直接 CRUD 操作
    comment_service = CommentService()
    
    try:
        # 恢复评论
        restored_comment = await comment_service.restore_comment(comment_id)
        return restored_comment
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )

@router.post("/guest-notice")
@public_endpoint(custom_message="获取游客评论提示失败")
async def guest_comment_notice(request: Request):
    """游客评论提示
    
    当未登录用户尝试评论时，返回提示信息要求注册或登录。
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        dict: 包含提示消息的响应
    """
    return {
        "status": "error",
        "message": "请先注册或登录后再发表评论",
        "detail": "评论功能仅对已登录用户开放，请注册新账号或登录后再尝试"
    }

@router.get("/post/{post_id}", response_model=CommentListResponse)
@public_endpoint(cache_ttl=60, custom_message="获取帖子评论失败")
async def get_comments_by_post(
    request: Request,
    post_id: int,
    skip: int = 0,
    limit: int = 100
):
    """获取帖子下的评论列表
    
    获取指定帖子下的所有评论，支持分页。
    此接口对所有用户开放，结果将被缓存1分钟。
    
    Args:
        request: FastAPI请求对象
        post_id: 帖子ID
        skip: 分页偏移量，默认0
        limit: 每页数量，默认100
        
    Returns:
        CommentListResponse: 评论列表
        
    Raises:
        HTTPException: 当获取评论失败时抛出相应错误
    """
    try:
        # 使用Service架构
        comment_service = CommentService()
        
        # 获取评论列表
        comments, total = await comment_service.get_comments_by_post(
            post_id=post_id,
            skip=skip,
            limit=limit
        )
        
        # 构建符合CommentListResponse的返回结构
        return {
            "comments": comments,
            "total": total,
            "post_id": post_id
        }
    except BusinessException as e:
        # 将业务异常转换为HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "error_code": e.error_code}
        )
