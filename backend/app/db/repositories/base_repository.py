from __future__ import annotations
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict, Tuple, Union
from datetime import datetime
from sqlalchemy import select, delete, func
# from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from pydantic import BaseModel

from ...core.database import Base, async_get_db, AsyncSessionLocal
from sqlalchemy.exc import SQLAlchemyError
from ...schemas.base import BaseSchema, DeleteResponse
# from ...schemas.responses.user import UserResponse
# from ...schemas.responses.post import PostResponse
# from ...schemas.responses.comment import CommentResponse
# from ...schemas.responses.category import CategoryResponse
# from ...schemas.responses.section import SectionResponse
# from ...schemas.responses.tag import TagResponse

ModelType = TypeVar("ModelType", bound=Base) # type: ignore
SchemaType = TypeVar("SchemaType", bound=BaseSchema)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, SchemaType]):
    """基础数据访问层"""
    
    def __init__(self, model: Type[ModelType], schema: Type[SchemaType]):
        """初始化
        
        Args:
            model: SQLAlchemy模型类
            schema: Pydantic响应模型类
        """
        self.model = model
        self.schema = schema
    
    def to_schema(self, model_instance: Optional[ModelType]) -> Optional[SchemaType]:
        """将模型实例转换为schema对象
        
        Args:
            model_instance: 数据库模型实例
            
        Returns:
            Optional[SchemaType]: schema对象，如果输入为None则返回None
        """
        if not model_instance:
            return None
        
        return self.schema.model_validate(model_instance)
    
    async def create(self, data: Union[Dict[str, Any], CreateSchemaType]) -> SchemaType:
        """创建记录
        
        Args:
            data: 创建数据字典或Pydantic模型
            
        Returns:
            SchemaType: 创建的记录
        """
        # 如果输入是Pydantic模型，将其转换为字典
        if isinstance(data, BaseModel):
            data_dict = data.model_dump(exclude_unset=True)
        else:
            data_dict = data
            
        async with async_get_db() as db:
            try:
                item = self.model(**data_dict)
                db.add(item)
                await db.commit()
                await db.refresh(item)
                return self.to_schema(item)
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def get(self, id: Any) -> Optional[SchemaType]:
        """获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[SchemaType]: 查询到的记录，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) &
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                return self.to_schema(item)
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def update(
        self,
        id: Any,
        data: Union[Dict[str, Any], UpdateSchemaType]
    ) -> Optional[SchemaType]:
        """更新记录
        
        Args:
            id: 记录ID
            data: 更新数据字典或Pydantic模型
            
        Returns:
            Optional[SchemaType]: 更新后的记录，不存在则返回None
        """
        # 如果输入是Pydantic模型，将其转换为字典
        if isinstance(data, BaseModel):
            data_dict = data.model_dump(exclude_unset=True)
        else:
            data_dict = data
            
        # 确保更新时间字段存在
        if "updated_at" not in data_dict:
            data_dict["updated_at"] = datetime.now()
            
        async with async_get_db() as db:
            try:
                # 获取要更新的对象
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) &
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    return None
                
                # 更新对象
                for key, value in data_dict.items():
                    setattr(item, key, value)
                
                await db.commit()
                await db.refresh(item)
                return self.to_schema(item)
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def delete(self, id: Any) -> Optional[DeleteResponse]:
        """软删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[DeleteResponse]: 删除结果，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                # 获取要软删除的对象
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) &
                        (self.model.is_deleted == False)
                    )
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    return None
                
                # 软删除
                setattr(item, "is_deleted", True)
                setattr(item, "deleted_at", datetime.now())
                
                await db.commit()
                
                # 返回删除响应
                return DeleteResponse(id=id, message=f"{self.model.__name__}已成功删除")
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def hard_delete(self, id: Any) -> bool:
        """硬删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否成功删除
        """
        async with async_get_db() as db:
            try:
                query = delete(self.model).where(self.model.id == id)
                result = await db.execute(query)
                await db.commit()
                return result.rowcount > 0
            except SQLAlchemyError as e:
                await db.rollback()
                raise e
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_deleted: bool = True
    ) -> List[SchemaType]:
        """获取所有记录
        
        Args:
            skip: 跳过条数
            limit: 限制条数
            filter_deleted: 是否过滤已删除的记录
            
        Returns:
            List[SchemaType]: 记录列表
        """
        async with async_get_db() as db:
            try:
                query = select(self.model)
                
                if filter_deleted:
                    query = query.where(self.model.is_deleted == False)
                
                query = query.offset(skip).limit(limit)
                
                result = await db.execute(query)
                items = result.scalars().all()
                
                return [self.to_schema(item) for item in items]
            except SQLAlchemyError as e:
                raise e
    
    async def count(self, filter_deleted: bool = True) -> int:
        """获取记录总数
        
        Args:
            filter_deleted: 是否过滤已删除的记录
            
        Returns:
            int: 记录总数
        """
        async with async_get_db() as db:
            try:
                query = select(func.count()).select_from(self.model)
                
                if filter_deleted:
                    query = query.where(self.model.is_deleted == False)
                
                result = await db.execute(query)
                return result.scalar_one()
            except SQLAlchemyError as e:
                raise e
    
    async def get_multi_paginated(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_deleted: bool = True
    ) -> Tuple[List[SchemaType], int]:
        """获取分页记录
        
        Args:
            skip: 跳过条数
            limit: 限制条数
            filter_deleted: 是否过滤已删除的记录
            
        Returns:
            Tuple[List[SchemaType], int]: 记录列表和总数
        """
        items = await self.get_all(skip, limit, filter_deleted)
        count = await self.count(filter_deleted)
        
        return items, count
    
    async def restore(self, id: Any) -> Optional[SchemaType]:
        """恢复被删除的记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[SchemaType]: 恢复后的记录，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                # 获取要恢复的对象
                result = await db.execute(
                    select(self.model).where(
                        (self.model.id == id) &
                        (self.model.is_deleted == True)
                    )
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    return None
                
                # 恢复
                setattr(item, "is_deleted", False)
                setattr(item, "deleted_at", None)
                setattr(item, "updated_at", datetime.now())
                
                await db.commit()
                await db.refresh(item)
                return self.to_schema(item)
            except SQLAlchemyError as e:
                await db.rollback()
                raise e 