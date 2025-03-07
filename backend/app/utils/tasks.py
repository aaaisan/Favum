from typing import Any, Optional, Dict, List
from celery.result import AsyncResult # type: ignore
from ..core.celery_config import celery_app
from ..core.logging import get_logger
from ..core.decorators import (
    handle_exceptions,
    log_execution_time,
    log_exception,
    retry
)

logger = get_logger(__name__)

class TaskManager:
    """任务管理器"""
    
    @staticmethod
    @log_execution_time
    @log_exception()
    def get_task_status(task_id: str) -> dict:
        """获取任务状态"""
        logger.info(f"获取任务状态: {task_id}")
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    
    @staticmethod
    @log_execution_time
    @log_exception()
    def revoke_task(task_id: str, terminate: bool = False) -> None:
        """取消任务"""
        logger.info(f"取消任务: {task_id}, terminate: {terminate}")
        celery_app.control.revoke(task_id, terminate=terminate)
    
    @staticmethod
    @log_execution_time
    @retry(max_retries=3, delay=1)
    @log_exception()
    def retry_task(task_id: str) -> None:
        """重试任务"""
        logger.info(f"重试任务: {task_id}")
        result = AsyncResult(task_id, app=celery_app)
        result.retry()
    
    @staticmethod
    @log_execution_time
    @log_exception()
    def get_active_tasks() -> list:
        """获取活动任务"""
        logger.info("获取活动任务列表")
        inspector = celery_app.control.inspect()
        active = inspector.active()
        return active if active else []
    
    @staticmethod
    @log_execution_time
    @retry(max_retries=3, delay=1)
    @log_exception()
    def get_task_info(task_id: str) -> Optional[dict]:
        """获取任务详细信息"""
        logger.info(f"获取任务详情: {task_id}")
        result = AsyncResult(task_id, app=celery_app)
        if not result:
            return None
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "date_done": result.date_done,
            "runtime": result.runtime if result.ready() else None,
        }
    
    @staticmethod
    @log_execution_time
    @log_exception()
    def list_tasks(
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取任务列表"""
        logger.info(f"获取任务列表: type={task_type}, skip={skip}, limit={limit}")
        inspector = celery_app.control.inspect()
        scheduled = inspector.scheduled() or {}
        reserved = inspector.reserved() or {}
        active = inspector.active() or {}
        
        all_tasks = []
        for worker, tasks in active.items():
            for task in tasks:
                if task_type and task.get("type") != task_type:
                    continue
                task["worker"] = worker
                task["state"] = "active"
                all_tasks.append(task)
                
        for worker, tasks in scheduled.items():
            for task in tasks:
                if task_type and task.get("type") != task_type:
                    continue
                task["worker"] = worker
                task["state"] = "scheduled"
                all_tasks.append(task)
                
        for worker, tasks in reserved.items():
            for task in tasks:
                if task_type and task.get("type") != task_type:
                    continue
                task["worker"] = worker
                task["state"] = "reserved"
                all_tasks.append(task)
        
        # 应用分页
        start = skip
        end = skip + limit
        return all_tasks[start:end]
    
    @staticmethod
    @log_execution_time
    @log_exception()
    def get_worker_stats() -> Dict[str, Any]:
        """获取工作器统计信息"""
        logger.info("获取工作器统计信息")
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
    
    @staticmethod
    @log_execution_time
    @retry(max_retries=2, delay=5)
    @log_exception()
    def cleanup_tasks() -> None:
        """清理过期任务"""
        logger.info("清理过期任务")
        # 这里可以添加清理过期任务的逻辑
        # 例如：清理已完成的任务、失败的任务等
        pass 