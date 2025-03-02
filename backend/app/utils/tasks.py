from typing import Any, Optional
from celery.result import AsyncResult # type: ignore
from ..core.celery_config import celery_app

class TaskManager:
    """任务管理器"""
    
    @staticmethod
    def get_task_status(task_id: str) -> dict:
        """获取任务状态"""
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    
    @staticmethod
    def revoke_task(task_id: str, terminate: bool = False) -> None:
        """取消任务"""
        celery_app.control.revoke(task_id, terminate=terminate)
    
    @staticmethod
    def retry_task(task_id: str) -> None:
        """重试任务"""
        result = AsyncResult(task_id, app=celery_app)
        result.retry()
    
    @staticmethod
    def get_active_tasks() -> list:
        """获取活动任务"""
        inspector = celery_app.control.inspect()
        active = inspector.active()
        return active if active else []
    
    @staticmethod
    def get_task_info(task_id: str) -> Optional[dict]:
        """获取任务详细信息"""
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