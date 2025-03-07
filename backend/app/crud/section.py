from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..db.models import Section, User, SectionModerator
from ..schemas import section as section_schema
from typing import List
from datetime import datetime

def get_section(db: Session, section_id: int):
    return db.query(Section).filter(Section.id == section_id).first()

def get_sections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Section).offset(skip).limit(limit).all()

def create_section(db: Session, section: section_schema.SectionCreate):
    db_section = Section(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def update_section(db: Session, section_id: int, section: section_schema.SectionUpdate):
    db_section = get_section(db, section_id)
    update_data = section.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_section, field, value)
    db.commit()
    db.refresh(db_section)
    return db_section

def add_moderator(db: Session, section_id: int, user_id: int):
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="版块不存在")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role != "moderator":
        user.role = "moderator"
    
    db_moderator = SectionModerator(section_id=section_id, user_id=user_id)
    db.add(db_moderator)
    db.commit()
    return {"detail": "版主添加成功"}

def remove_moderator(db: Session, section_id: int, user_id: int):
    """将用户从版块版主中移除"""
    # 验证版块存在
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="版块不存在")
    
    # 验证用户作为版主的记录存在
    db_moderator = db.query(SectionModerator).filter(
        SectionModerator.section_id == section_id,
        SectionModerator.user_id == user_id
    ).first()
    
    if not db_moderator:
        raise HTTPException(status_code=404, detail="该用户不是此版块的版主")
    
    # 使用软删除代替物理删除
    db_moderator.is_deleted = True
    db.add(db_moderator)
    
    # 检查用户是否还是其他版块的版主
    other_sections = db.query(SectionModerator).filter(
        SectionModerator.user_id == user_id,
        SectionModerator.is_deleted == False,
        SectionModerator.section_id != section_id
    ).first()
    
    if not other_sections:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "moderator":
            user.role = "user"
    
    db.commit()
    return {"detail": "版主已移除"}

def restore_moderator(db: Session, section_id: int, user_id: int):
    """恢复已删除的版主
    
    Args:
        db: 数据库会话
        section_id: 版块ID
        user_id: 用户ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果版块不存在、用户不存在、记录不存在或未被删除则抛出相应错误
    """
    # 验证版块存在
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="版块不存在")
    
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证用户作为版主的记录存在且已被删除
    db_moderator = db.query(SectionModerator).filter(
        SectionModerator.section_id == section_id,
        SectionModerator.user_id == user_id
    ).first()
    
    if not db_moderator:
        raise HTTPException(status_code=404, detail="未找到相关版主记录")
    
    if not db_moderator.is_deleted:
        raise HTTPException(status_code=400, detail="该用户已是此版块的版主")
    
    # 恢复版主记录
    db_moderator.is_deleted = False
    db.add(db_moderator)
    
    # 更新用户角色为版主
    if user.role != "moderator" and user.role != "admin" and user.role != "super_admin":
        user.role = "moderator"
    
    db.commit()
    return {"detail": "版主已恢复"}

def delete_section(db: Session, section_id: int):
    """软删除版块
    
    Args:
        db: 数据库会话
        section_id: 版块ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果版块不存在则抛出404错误
    """
    db_section = get_section(db, section_id)
    if not db_section:
        raise HTTPException(status_code=404, detail="版块不存在")
    
    # 使用软删除代替物理删除
    db_section.is_deleted = True
    
    # 如果有deleted_at字段，设置删除时间
    if hasattr(db_section, "deleted_at"):
        db_section.deleted_at = datetime.now()
    
    db.add(db_section)
    db.commit()
    return {"detail": "版块已删除"}

def restore_section(db: Session, section_id: int):
    """恢复已删除的版块
    
    Args:
        db: 数据库会话
        section_id: 版块ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果版块不存在则抛出404错误，如果版块未被删除则抛出400错误
    """
    # 查找版块，包括已删除的
    db_section = db.query(Section).filter(Section.id == section_id).first()
    
    # 如果版块不存在，抛出404错误
    if not db_section:
        raise HTTPException(status_code=404, detail="版块不存在")
    
    # 如果版块未被删除，抛出400错误
    if not db_section.is_deleted:
        raise HTTPException(status_code=400, detail="版块未被删除")
    
    # 恢复版块
    db_section.is_deleted = False
    db_section.deleted_at = None
    
    # 提交更改
    db.add(db_section)
    db.commit()
    
    return {"detail": "版块已恢复"} 