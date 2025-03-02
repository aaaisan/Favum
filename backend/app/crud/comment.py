from sqlalchemy.orm import Session
from ..db.models import Comment
from ..schemas import comment as comment_schema
from fastapi import HTTPException
from datetime import datetime

def get_comment(db: Session, comment_id: int):
    return db.query(Comment).filter(Comment.id == comment_id).first()

def get_comments_by_post(db: Session, post_id: int, skip: int = 0, limit: int = 100):
    return db.query(Comment).filter(Comment.post_id == post_id).offset(skip).limit(limit).all()

def create_comment(db: Session, comment: comment_schema.CommentCreate):
    db_comment = Comment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def delete_comment(db: Session, comment_id: int):
    db_comment = get_comment(db, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 使用软删除代替物理删除
    db_comment.is_deleted = True
    
    # 如果有deleted_at字段，设置删除时间
    if hasattr(db_comment, "deleted_at"):
        db_comment.deleted_at = datetime.now()
    
    db.add(db_comment)
    db.commit()
    return {"detail": "评论已删除"}

def restore_comment(db: Session, comment_id: int):
    """恢复已删除的评论
    
    Args:
        db: 数据库会话
        comment_id: 评论ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果评论不存在则抛出404错误，如果评论未被删除则抛出400错误
    """
    # 查找评论，包括已删除的
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    # 如果评论不存在，抛出404错误
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 如果评论未被删除，抛出400错误
    if not db_comment.is_deleted:
        raise HTTPException(status_code=400, detail="评论未被删除")
    
    # 恢复评论
    db_comment.is_deleted = False
    db_comment.deleted_at = None
    
    # 提交更改
    db.add(db_comment)
    db.commit()
    
    return {"detail": "评论已恢复"} 