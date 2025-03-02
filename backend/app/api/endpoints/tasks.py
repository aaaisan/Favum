from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import logging

from ...core.auth import get_current_active_user
from ...core.permissions import Permission, Role
from ...core.decorators import (
    handle_exceptions,
    rate_limit,
    cache,
    validate_token,
    log_execution_time,
    require_permissions,
    require_roles
)

from ...db.models.task import Task
from ...utils.tasks import TaskManager
from ...services.task_service import task_service, TaskService
from ...schemas.task import TaskResponse
from .base import BaseEndpoint
from ...schemas.task import (
    TaskCreate,
    TaskUpdate
)

router = APIRouter()

# 创建任务API端点
task_endpoint = BaseEndpoint(
    router=router,
    prefix="/tasks",
    tags=["tasks"],
    service=TaskService,
    response_model=TaskResponse,
    create_schema=TaskCreate,
    update_schema=TaskUpdate
)

@router.get("/status/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务状态失败", include_details=True)
@validate_token
@require_permissions(Permission.VIEW_TASKS)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_task_status(request: Request, task_id: str):
    """获取任务状态"""
    task_info = await task_endpoint.service.get_task_info(task_id)
    if not task_info:
        raise HTTPException(
            status_code=404,
            detail="任务不存在"
        )
    return task_info

@router.get("/info/{task_id}")
async def get_task_info(
    task_id: str,
    _: dict = Depends(get_current_active_user)
):
    """获取任务详细信息"""
    info = TaskManager.get_task_info(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="任务不存在")
    return info

@router.get("/active", response_model=List[dict])
async def get_active_tasks(
    _: dict = Depends(get_current_active_user)
):
    """获取所有活动任务"""
    return TaskManager.get_active_tasks()

@router.post("/revoke/{task_id}")
async def revoke_task(
    task_id: str,
    terminate: bool = False,
    _: dict = Depends(get_current_active_user)
):
    """取消任务"""
    TaskManager.revoke_task(task_id, terminate)
    return {"detail": "任务已取消"}

@router.post("/retry/{task_id}")
async def retry_task(
    task_id: str,
    _: dict = Depends(get_current_active_user)
):
    """重试任务"""
    TaskManager.retry_task(task_id)
    return {"detail": "任务已重新提交"}

@router.get("/list")
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务列表失败", include_details=True)
@validate_token
@require_permissions(Permission.VIEW_TASKS)
@cache(expire=60, include_query_params=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def list_tasks(
    request: Request,
    task_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
):
    """获取任务列表"""
    return await task_endpoint.service.list_tasks(
        task_type=task_type,
        limit=limit,
        skip=skip
    )

@router.post("/register")
@handle_exceptions(SQLAlchemyError, status_code=500, message="注册任务失败", include_details=True)
@validate_token
@require_permissions([Permission.MANAGE_TASKS, Permission.EXECUTE_TASKS], require_all=True)
@rate_limit(limit=10, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def register_task(request: Request, task_data: dict):
    """注册新任务"""
    return await task_endpoint.service.create(task_data)

@router.delete("/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除任务失败", include_details=True)
@validate_token
@require_permissions(Permission.MANAGE_TASKS)
@rate_limit(limit=20, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def delete_task(request: Request, task_id: str):
    """删除任务"""
    await task_endpoint.service.delete(task_id)
    return {"message": "任务已删除"}

@router.get("/stats")
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取统计信息失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@cache(expire=30, include_query_params=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_worker_stats(request: Request):
    """获取工作器统计信息"""
    return await task_endpoint.service.get_worker_stats() 