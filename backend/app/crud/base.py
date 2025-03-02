from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from ..db.models import Base
from ..db.query import QueryOptimizer

ModelType = TypeVar("ModelType", bound="Base")
CreateSchemaType = TypeVar("CreateSchemaType", bound="BaseModel")
UpdateSchemaType = TypeVar("UpdateSchemaType", bound="BaseModel")

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础CRUD操作类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.query_optimizer = QueryOptimizer()
    
    def get(
        self,
        db: Session,
        id: Any
    ) -> Optional[ModelType]:
        """获取记录"""
        query = db.query(self.model).filter(self.model.id == id)
        # 排除已删除的记录
        if hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted == False)
        return query.first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """获取多条记录"""
        query = db.query(self.model)
        
        # 排除已删除的记录（除非明确要求包含）
        if hasattr(self.model, "is_deleted") and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
            
        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)
        
        return query.offset(skip).limit(limit).all()
    
    def create(
        self,
        db: Session,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """创建记录"""
        obj_in_data = jsonable_encoder(obj_in) if not isinstance(obj_in, dict) else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新记录"""
        # 验证记录未被删除
        if hasattr(db_obj, "is_deleted") and db_obj.is_deleted:
            return None
            
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(
        self,
        db: Session,
        *,
        id: Any
    ) -> ModelType:
        """软删除记录"""
        obj = db.query(self.model).get(id)
        if not obj:
            return None
            
        # 如果没有is_deleted字段，抛出异常
        if not hasattr(obj, "is_deleted"):
            raise ValueError(f"模型 {self.model.__name__} 不支持软删除，缺少 is_deleted 字段")
            
        # 软删除：设置is_deleted为True
        setattr(obj, "is_deleted", True)
        
        # 如果有deleted_at字段，设置删除时间
        if hasattr(obj, "deleted_at"):
            setattr(obj, "deleted_at", datetime.now())
            
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    
    def restore(
        self,
        db: Session,
        *,
        id: Any
    ) -> ModelType:
        """恢复软删除的记录"""
        # 获取记录，包括已删除的
        obj = db.query(self.model).get(id)
        if not obj:
            return None
            
        # 如果没有is_deleted字段，抛出异常
        if not hasattr(obj, "is_deleted"):
            raise ValueError(f"模型 {self.model.__name__} 不支持软删除，缺少 is_deleted 字段")
            
        # 如果记录未被删除，无需操作
        if not obj.is_deleted:
            return obj
            
        # 恢复记录：设置is_deleted为False
        setattr(obj, "is_deleted", False)
        
        # 如果有deleted_at字段，清除删除时间
        if hasattr(obj, "deleted_at"):
            setattr(obj, "deleted_at", None)
            
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
        
    def hard_remove(
        self,
        db: Session,
        *,
        id: Any
    ) -> ModelType:
        """物理删除记录（谨慎使用，仅用于管理员操作或测试）"""
        # 首先检查是否有软删除字段，如果有，建议使用软删除
        obj = db.query(self.model).get(id)
        if obj and hasattr(obj, "is_deleted"):
            print(f"警告: 模型 {self.model.__name__} 支持软删除，建议使用 remove() 方法代替 hard_remove()")
        
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def exists(
        self,
        db: Session,
        id: Any
    ) -> bool:
        """检查记录是否存在（且未被删除）"""
        query = db.query(self.model).filter(self.model.id == id)
        # 验证记录未被删除
        if hasattr(self.model, "is_deleted"):
            query = query.filter(self.model.is_deleted == False)
        return db.query(query.exists()).scalar()
    
    def count(
        self,
        db: Session,
        filters: Optional[List[Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """获取记录数量"""
        query = db.query(self.model)
        
        # 排除已删除的记录
        if hasattr(self.model, "is_deleted") and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
            
        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)
        return query.count() 