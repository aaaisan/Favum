"""
任务服务

提供任务相关的业务逻辑实现，包括：
- 任务的创建、查询、更新和删除
- 任务调度和执行管理
- 任务状态监控和历史记录查询

该服务层依赖于TaskRepository进行数据访问，以及CeleryApp进行任务调度。
"""

from typing import Any, Dict, List, Optional
from celery.result import AsyncResult

from ..db.repositories.task_repository import TaskRepository
from ..core.celery_config import celery_app
from ..core.exceptions import BusinessException
from ..core.logging import get_logger

logger = get_logger(__name__)

class TaskService:
    """任务业务逻辑服务"""
    
    def __init__(self):
        """初始化任务服务
        
        创建TaskRepository实例
        """
        self.repository = TaskRepository()
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新任务
        
        Args:
            task_data: 任务数据，包含名称、类型、描述等信息
            
        Returns:
            Dict[str, Any]: 创建的任务信息
            
        Raises:
            BusinessException: 当任务名称已存在或创建失败时抛出
        """
        # 检查任务名称是否已存在
        existing_task = await self.repository.get_task(task_data.get("name", ""))
        if existing_task:
            raise BusinessException(
                status_code=400,
                error_code="TASK_ALREADY_EXISTS",
                message="任务名称已存在"
            )
        
        # 创建任务
        return await self.repository.create_task(task_data)
    
    async def get_task(self, name: str) -> Dict[str, Any]:
        """获取任务详情
        
        Args:
            name: 任务名称
            
        Returns:
            Dict[str, Any]: 任务详情
            
        Raises:
            BusinessException: 当任务不存在时抛出
        """
        task = await self.repository.get_task(name)
        if not task:
            raise BusinessException(
                status_code=404,
                error_code="TASK_NOT_FOUND",
                message="任务不存在"
            )
        return task
    
    async def update_task(self, name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务
        
        Args:
            name: 任务名称
            task_data: 更新的任务数据
            
        Returns:
            Dict[str, Any]: 更新后的任务信息
            
        Raises:
            BusinessException: 当任务不存在或更新失败时抛出
        """
        # 检查任务是否存在
        await self.get_task(name)
        
        # 更新任务
        return await self.repository.update_task(name, task_data)
    
    async def delete_task(self, name: str) -> Dict[str, Any]:
        """删除任务（软删除）
        
        Args:
            name: 任务名称
            
        Returns:
            Dict[str, Any]: 删除结果
            
        Raises:
            BusinessException: 当任务不存在或删除失败时抛出
        """
        # 检查任务是否存在
        await self.get_task(name)
        
        # 删除任务
        return await self.repository.delete_task(name)
    
    async def list_tasks(
        self,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取任务列表
        
        Args:
            task_type: 任务类型，可选过滤条件
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        return await self.repository.list_tasks(task_type, skip, limit)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    
    async def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作器统计信息
        
        Returns:
            Dict[str, Any]: 工作器统计信息
        """
        inspector = celery_app.control.inspect()
        stats = inspector.stats() or {}
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        reserved = inspector.reserved() or {}
        
        return {
            "workers": len(stats),
            "stats": stats,
            "tasks": {
                "active": sum(len(tasks) for tasks in active.values()),
                "scheduled": sum(len(tasks) for tasks in scheduled.values()),
                "reserved": sum(len(tasks) for tasks in reserved.values())
            }
        }
    
    async def revoke_task(self, task_id: str, terminate: bool = False) -> None:
        """取消任务
        
        Args:
            task_id: 任务ID
            terminate: 是否终止任务
        """
        celery_app.control.revoke(task_id, terminate=terminate)
    
    async def retry_task(self, task_id: str) -> None:
        """重试任务
        
        Args:
            task_id: 任务ID
            
        Raises:
            BusinessException: 当任务不存在或重试失败时抛出
        """
        try:
            result = AsyncResult(task_id, app=celery_app)
            result.retry()
        except Exception as e:
            logger.error(f"重试任务失败: {e}")
            raise BusinessException(
                status_code=400,
                error_code="TASK_RETRY_FAILED",
                message=f"重试任务失败: {str(e)}"
            ) 