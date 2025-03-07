from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.task import Task
from ..database import get_db
from ...core.config import settings
from ...core.decorators import handle_exceptions, log_execution_time, retry
from sqlalchemy.exc import SQLAlchemyError

class TaskRepository:
    """任务数据访问层"""
    
    def __init__(self):
        self.db: AsyncSession = get_db()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="创建任务失败")
    @log_execution_time
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        task = Task(**task_data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task.to_dict()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def get_task(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        result = await self.db.execute(
            select(Task).where(
                (Task.name == name) & 
                (Task.is_deleted == False)
            )
        )
        task = result.scalar_one_or_none()
        return task.to_dict() if task else None
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="删除任务失败")
    @log_execution_time
    async def delete_task(self, name: str) -> None:
        """软删除任务"""
        # 检查任务是否存在且未删除
        result = await self.db.execute(
            select(Task).where(
                (Task.name == name) & 
                (Task.is_deleted == False)
            )
        )
        task = result.scalar_one_or_none()
        
        if task:
            # 执行软删除
            await self.db.execute(
                update(Task)
                .where(Task.name == name)
                .values(is_deleted=True, deleted_at=datetime.now())
            )
            await self.db.commit()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="删除任务失败")
    @log_execution_time
    async def hard_delete_task(self, name: str) -> None:
        """物理删除任务（谨慎使用）"""
        await self.db.execute(
            delete(Task).where(Task.name == name)
        )
        await self.db.commit()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="获取任务列表失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def list_tasks(
        self,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """获取任务列表"""
        query = select(Task)
        
        # 默认不包含已删除任务
        if not include_deleted:
            query = query.where(Task.is_deleted == False)
            
        if task_type:
            query = query.where(Task.type == task_type)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return [task.to_dict() for task in tasks]
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="获取过期任务失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def get_expired_tasks(self) -> List[Dict[str, Any]]:
        """获取过期任务"""
        expiry_time = datetime.now() - timedelta(
            hours=settings.TASK_EXPIRY_HOURS
        )
        
        query = select(Task).where(
            (Task.last_run < expiry_time) & 
            (Task.is_deleted == False)
        )
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return [task.to_dict() for task in tasks] 