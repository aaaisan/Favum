from __future__ import annotations
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.decorators.error import handle_exceptions, retry
from ...core.decorators.logging import log_execution_time
from ..database import Base, get_db
from sqlalchemy.exc import SQLAlchemyError

class BaseRepository:
    """基础数据访问层"""
    
    def __init__(self, model: Type[Base]):
        self.model = model
        self.db: AsyncSession = get_db()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @log_execution_time
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录"""
        item = self.model(**data)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item.to_dict()
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """获取记录"""
        result = await self.db.execute(
            select(self.model).where(
                (self.model.id == id) & 
                (self.model.is_deleted == False)
            )
        )
        item = result.scalar_one_or_none()
        return item.to_dict() if item else None
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @log_execution_time
    async def update(
        self,
        id: Any,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新记录"""
        result = await self.db.execute(
            update(self.model)
            .where(
                (self.model.id == id) & 
                (self.model.is_deleted == False)
            )
            .values(**data)
            .returning(self.model)
        )
        await self.db.commit()
        
        item = result.scalar_one_or_none()
        return item.to_dict() if item else None
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @log_execution_time
    async def delete(self, id: Any) -> bool:
        """软删除记录，将is_deleted设为True"""
        # 检查记录是否存在且未被删除
        get_result = await self.db.execute(
            select(self.model).where(
                (self.model.id == id) & 
                (self.model.is_deleted == False)
            )
        )
        item = get_result.scalar_one_or_none()
        if not item:
            return False
            
        # 如果存在deleted_at字段，则记录删除时间
        update_values = {"is_deleted": True}
        if hasattr(self.model, "deleted_at"):
            update_values["deleted_at"] = datetime.now()
            
        result = await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_values)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @log_execution_time
    async def restore(self, id: Any) -> bool:
        """恢复软删除的记录"""
        # 检查记录是否存在且已被删除
        get_result = await self.db.execute(
            select(self.model).where(
                (self.model.id == id) & 
                (self.model.is_deleted == True)
            )
        )
        item = get_result.scalar_one_or_none()
        if not item:
            return False
            
        # 清除软删除标记
        update_values = {"is_deleted": False}
        if hasattr(self.model, "deleted_at"):
            update_values["deleted_at"] = None
            
        result = await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_values)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @log_execution_time
    async def hard_delete(self, id: Any) -> bool:
        """物理删除记录（仅在特殊情况下使用）"""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        order: str = "asc",
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """获取记录列表"""
        query = select(self.model)
        
        # 默认不包含已删除记录
        if hasattr(self.model, "is_deleted") and not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        if sort_by and hasattr(self.model, sort_by):
            order_by = getattr(self.model, sort_by)
            if order.lower() == "desc":
                order_by = order_by.desc()
            query = query.order_by(order_by)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return [item.to_dict() for item in items]
    
    @handle_exceptions(SQLAlchemyError, status_code=500, message="数据库操作失败")
    @retry(max_retries=3, delay=1, exceptions=(SQLAlchemyError,))
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """获取记录数量"""
        query = select(func.count()).select_from(self.model)
        
        # 默认不包含已删除记录
        if hasattr(self.model, "is_deleted") and not include_deleted:
            query = query.where(self.model.is_deleted == False)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
                    
        result = await self.db.execute(query)
        return result.scalar_one() 