from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..db.models import Post, PostFavorite, User
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional

def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户收藏的帖子列表
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过数量
        limit: 返回数量限制
        
    Returns:
        dict: 包含帖子列表和总数的字典
    """
    # 查询用户收藏的帖子总数
    total = db.query(PostFavorite).filter(PostFavorite.user_id == user_id).count()
    
    # 查询用户收藏的帖子，带有完整的帖子信息
    favorites = db.query(Post).join(
        PostFavorite, PostFavorite.post_id == Post.id
    ).filter(
        PostFavorite.user_id == user_id,
        Post.is_hidden == False,  # 不包含隐藏的帖子
        Post.is_deleted == False  # 不包含已删除的帖子
    ).order_by(
        PostFavorite.created_at.desc()  # 按收藏时间倒序排列
    ).offset(skip).limit(limit).all()
    
    return {
        "posts": favorites,
        "total": total
    }

def is_post_favorited(db: Session, post_id: int, user_id: int) -> bool:
    """检查用户是否已经收藏了指定帖子
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        user_id: 用户ID
        
    Returns:
        bool: 如果用户已收藏该帖子则返回True，否则返回False
    """
    favorite = db.query(PostFavorite).filter(
        PostFavorite.post_id == post_id,
        PostFavorite.user_id == user_id
    ).first()
    
    return favorite is not None

def add_favorite(db: Session, post_id: int, user_id: int):
    """添加帖子到用户收藏
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        user_id: 用户ID
        
    Returns:
        dict: 包含操作结果和消息的字典
        
    Raises:
        HTTPException: 如果帖子不存在或操作失败
    """
    # 检查帖子是否存在且未被隐藏或删除
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.is_deleted == False
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在或已被删除")
    
    # 检查用户是否已经收藏了该帖子
    if is_post_favorited(db, post_id, user_id):
        return {
            "success": False,
            "message": "您已经收藏过该帖子"
        }
    
    # 创建新的收藏记录
    favorite = PostFavorite(
        post_id=post_id,
        user_id=user_id
    )
    
    try:
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return {
            "success": True,
            "message": "收藏成功"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="收藏失败，请稍后重试")

def remove_favorite(db: Session, post_id: int, user_id: int):
    """从用户收藏中移除帖子
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        user_id: 用户ID
        
    Returns:
        dict: 包含操作结果和消息的字典
    """
    # 查找收藏记录
    favorite = db.query(PostFavorite).filter(
        PostFavorite.post_id == post_id,
        PostFavorite.user_id == user_id
    ).first()
    
    if not favorite:
        return {
            "success": False,
            "message": "您尚未收藏该帖子"
        }
    
    # 删除收藏记录
    db.delete(favorite)
    db.commit()
    
    return {
        "success": True,
        "message": "已取消收藏"
    } 