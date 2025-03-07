from __future__ import annotations
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import Base, get_db
from sqlalchemy.exc import SQLAlchemyError

class BaseRepository:
    """基础数据访问层"""
    
    def __init__(self, model: Type[Base]): # type: ignore
        self.model = model
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录"""
        async with get_db() as db:
            try:
                item = self.model(**data)  # type: ignore
                db.add(item)
                await db.commit()
                await db.refresh(item)
                return item.to_dict()
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """获取记录"""
        async with get_db() as db:
            try:
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) & 
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                if not item:
                    return None
                return item.to_dict()
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def update(
        self,
        id: Any,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新记录"""
        async with get_db() as db:
            try:
                # 首先检查记录是否存在
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) & 
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                if not item:
                    return None
                
                # 更新记录
                for key, value in data.items():
                    setattr(item, key, value)
                
                item.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(item)
                return item.to_dict()
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def delete(self, id: Any) -> bool:
        """软删除记录"""
        async with get_db() as db:
            try:
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) & 
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                if not item:
                    return False
                
                item.is_deleted = True
                item.deleted_at = datetime.utcnow()
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def restore(self, id: Any) -> bool:
        """恢复删除的记录"""
        async with get_db() as db:
            try:
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) & 
                        (self.model.is_deleted == True)
                    )
                )
                item = result.scalar_one_or_none()
                if not item:
                    return False
                
                item.is_deleted = False
                item.deleted_at = None
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def hard_delete(self, id: Any) -> bool:
        """硬删除记录"""
        async with get_db() as db:
            try:
                result = await db.execute(
                    select(self.model).where(self.model.id == id)
                )
                item = result.scalar_one_or_none()
                if not item:
                    return False
                
                await db.delete(item)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
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
        async with get_db() as db:
            try:
                query = select(self.model)
                
                # 应用过滤条件
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model, field):
                            query = query.where(getattr(self.model, field) == value)
                
                # 是否包含已删除的记录
                if not include_deleted and hasattr(self.model, "is_deleted"):
                    query = query.where(self.model.is_deleted == False)
                
                # 排序
                if sort_by and hasattr(self.model, sort_by):
                    sort_field = getattr(self.model, sort_by)
                    if order.lower() == "desc":
                        query = query.order_by(sort_field.desc())
                    else:
                        query = query.order_by(sort_field.asc())
                
                # 分页
                query = query.offset(skip).limit(limit)
                
                result = await db.execute(query)
                items = result.scalars().all()
                return [item.to_dict() for item in items]
            except SQLAlchemyError as e:
                raise e
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """获取记录数量"""
        async with get_db() as db:
            try:
                query = select(func.count(self.model.id))
                
                # 应用过滤条件
                if filters:
                    for field, value in filters.items():
                        if hasattr(self.model, field):
                            query = query.where(getattr(self.model, field) == value)
                
                # 是否包含已删除的记录
                if not include_deleted and hasattr(self.model, "is_deleted"):
                    query = query.where(self.model.is_deleted == False)
                
                result = await db.execute(query)
                return result.scalar_one()
            except SQLAlchemyError as e:
                raise e 