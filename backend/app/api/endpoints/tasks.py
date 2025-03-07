from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import logging

from ...core.auth import get_current_active_user
from ...core.permissions import Permission, Role
from ...core.decorators.error import handle_exceptions
from ...core.decorators.auth import validate_token, require_permissions, require_roles
from ...core.decorators.performance import rate_limit, cache
from ...core.decorators.logging import log_execution_time

from ...db.models.task import Task
from ...utils.tasks import TaskManager
from ...schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse
)

router = APIRouter()

@router.post("/", response_model=TaskResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="创建任务失败", include_details=True)
@validate_token
@require_permissions([Permission.MANAGE_TASKS, Permission.EXECUTE_TASKS], require_all=True)
@rate_limit(limit=10, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def create_task(
    request: Request,
    task: TaskCreate
):
    """创建新任务"""
    return await TaskManager.create_task(task.dict())

@router.get("/", response_model=List[TaskResponse])
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
    return await TaskManager.list_tasks(
        task_type=task_type,
        limit=limit,
        skip=skip
    )

@router.get("/{task_id}", response_model=TaskResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务详情失败", include_details=True)
@validate_token
@require_permissions(Permission.VIEW_TASKS)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_task(
    request: Request,
    task_id: str
):
    """获取任务详情"""
    task = await TaskManager.get_task_info(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
@handle_exceptions(SQLAlchemyError, status_code=500, message="更新任务失败", include_details=True)
@validate_token
@require_permissions(Permission.MANAGE_TASKS)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def update_task(
    request: Request,
    task_id: str,
    task: TaskUpdate
):
    """更新任务"""
    updated_task = await TaskManager.update_task(task_id, task.dict(exclude_unset=True))
    if not updated_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return updated_task

@router.delete("/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="删除任务失败", include_details=True)
@validate_token
@require_permissions(Permission.MANAGE_TASKS)
@rate_limit(limit=20, window=60)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def delete_task(
    request: Request,
    task_id: str
):
    """删除任务"""
    await TaskManager.delete_task(task_id)
    return {"message": "任务已删除"}

@router.get("/status/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务状态失败", include_details=True)
@validate_token
@require_permissions(Permission.VIEW_TASKS)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_task_status(
    request: Request,
    task_id: str
):
    """获取任务状态"""
    return await TaskManager.get_task_status(task_id)

@router.get("/active", response_model=List[dict])
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取活动任务失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_active_tasks(
    request: Request
):
    """获取所有活动任务"""
    return await TaskManager.get_active_tasks()

@router.post("/revoke/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="取消任务失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def revoke_task(
    request: Request,
    task_id: str,
    terminate: bool = False
):
    """取消任务"""
    await TaskManager.revoke_task(task_id, terminate)
    return {"detail": "任务已取消"}

@router.post("/retry/{task_id}")
@handle_exceptions(SQLAlchemyError, status_code=500, message="重试任务失败", include_details=True)
@validate_token
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def retry_task(
    request: Request,
    task_id: str
):
    """重试任务"""
    await TaskManager.retry_task(task_id)
    return {"detail": "任务已重新提交"}

@router.get("/stats")
@handle_exceptions(SQLAlchemyError, status_code=500, message="获取统计信息失败", include_details=True)
@validate_token
@require_roles([Role.ADMIN, Role.SUPER_ADMIN])
@cache(expire=30, include_query_params=True)
@log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
async def get_worker_stats(request: Request):
    """获取工作器统计信息"""
    return await TaskManager.get_worker_stats() 