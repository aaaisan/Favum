from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from ..db.models import Category
from ..schemas import category as category_schema
from typing import Optional, List
from datetime import datetime

def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.order).offset(skip).limit(limit).all()

def create_category(db: Session, category: category_schema.CategoryCreate):
    if category.parent_id:
        parent = get_category(db, category.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分类不存在")
    
    # 如果没有指定order，则设置为当前最大order + 1
    if category.order is None:
        max_order = db.query(Category).filter(
            Category.parent_id == category.parent_id
        ).order_by(desc(Category.order)).first()
        category.order = (max_order.order + 1) if max_order else 0
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category: category_schema.CategoryUpdate):
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if category.parent_id and category.parent_id != db_category.parent_id:
        parent = get_category(db, category.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分类不存在")
        # 检查是否会形成循环引用
        if parent.id == category_id or any(c.id == category_id for c in parent.children):
            raise HTTPException(status_code=400, detail="不能将分类设置为其子分类的子分类")
    
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if db_category.children:
        raise HTTPException(status_code=400, detail="不能删除有子分类的分类")
    
    if db_category.posts:
        raise HTTPException(status_code=400, detail="不能删除有帖子的分类")
    
    # 使用软删除代替物理删除
    db_category.is_deleted = True
    
    # 如果有deleted_at字段，设置删除时间
    if hasattr(db_category, "deleted_at"):
        db_category.deleted_at = datetime.now()
    
    db.add(db_category)
    db.commit()
    return {"detail": "分类已删除"}

def restore_category(db: Session, category_id: int):
    """恢复已删除的分类
    
    Args:
        db: 数据库会话
        category_id: 分类ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果分类不存在则抛出404错误，如果分类未被删除则抛出400错误
    """
    # 查找分类，包括已删除的
    db_category = db.query(Category).filter(Category.id == category_id).first()
    
    # 如果分类不存在，抛出404错误
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 如果分类未被删除，抛出400错误
    if not db_category.is_deleted:
        raise HTTPException(status_code=400, detail="分类未被删除")
    
    # 检查父分类是否已删除
    if db_category.parent_id and db_category.parent.is_deleted:
        raise HTTPException(status_code=400, detail="父分类已被删除，请先恢复父分类")
    
    # 恢复分类
    db_category.is_deleted = False
    db_category.deleted_at = None
    
    # 提交更改
    db.add(db_category)
    db.commit()
    
    return {"detail": "分类已恢复"}

def reorder_categories(db: Session, parent_id: Optional[int], category_ids: List[int]):
    """重新排序分类"""
    categories = db.query(Category).filter(
        Category.id.in_(category_ids),
        Category.parent_id == parent_id
    ).all()
    
    if len(categories) != len(category_ids):
        raise HTTPException(status_code=400, detail="部分分类不存在或不属于同一父分类")
    
    for index, category_id in enumerate(category_ids):
        category = next(c for c in categories if c.id == category_id)
        category.order = index
    
    db.commit()
    return categories 