from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from fastapi import HTTPException
from ..db.models import Tag, Post
from ..schemas import tag as tag_schema

def get_tag(db: Session, tag_id: int):
    return db.query(Tag).filter(Tag.id == tag_id).first()

def get_tag_by_name(db: Session, name: str):
    return db.query(Tag).filter(Tag.name == name).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tag).offset(skip).limit(limit).all()

def get_popular_tags(db: Session, limit: int = 10):
    """获取最热门的标签"""
    return db.query(Tag).order_by(desc(Tag.post_count)).limit(limit).all()

def get_recent_tags(db: Session, limit: int = 10):
    """获取最近使用的标签"""
    return db.query(Tag).filter(Tag.last_used_at.isnot(None)).order_by(desc(Tag.last_used_at)).limit(limit).all()

def create_tag(db: Session, tag: tag_schema.TagCreate):
    db_tag = Tag(**tag.model_dump())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def update_tag(db: Session, tag_id: int, tag: tag_schema.TagUpdate):
    db_tag = get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    update_data = tag.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int):
    db_tag = get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    if db_tag.posts:
        raise HTTPException(status_code=400, detail="不能删除已被使用的标签")
    
    # 使用软删除代替物理删除
    db_tag.is_deleted = True
    
    # 如果有deleted_at字段，设置删除时间
    if hasattr(db_tag, "deleted_at"):
        db_tag.deleted_at = datetime.now()
    
    db.add(db_tag)
    db.commit()
    return {"detail": "标签已删除"}

def restore_tag(db: Session, tag_id: int):
    """恢复已删除的标签
    
    Args:
        db: 数据库会话
        tag_id: 标签ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果标签不存在则抛出404错误，如果标签未被删除则抛出400错误
    """
    # 查找标签，包括已删除的
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    # 如果标签不存在，抛出404错误
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 如果标签未被删除，抛出400错误
    if not db_tag.is_deleted:
        raise HTTPException(status_code=400, detail="标签未被删除")
    
    # 检查是否有同名未删除标签
    existing_tag = db.query(Tag).filter(
        Tag.name == db_tag.name,
        Tag.id != tag_id,
        Tag.is_deleted == False
    ).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="已存在同名标签，无法恢复")
    
    # 恢复标签
    db_tag.is_deleted = False
    db_tag.deleted_at = None
    
    # 提交更改
    db.add(db_tag)
    db.commit()
    
    return {"detail": "标签已恢复"}

def update_tag_stats(db: Session, tag_id: int):
    """更新标签的统计信息"""
    db_tag = get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 更新帖子数量
    post_count = db.query(func.count(Post.id)).join(Post.tags).filter(Tag.id == tag_id).scalar()
    db_tag.post_count = post_count
    
    # 更新最后使用时间
    if post_count > 0:
        db_tag.last_used_at = datetime.now()
    
    db.commit()
    db.refresh(db_tag)
    return db_tag 