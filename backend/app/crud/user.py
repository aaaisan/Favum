from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from ..db.models import User, Post
from ..schemas import user as user_schema
from ..core.security import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email, User.is_deleted == False).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username, User.is_deleted == False).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).filter(User.is_deleted == False).offset(skip).limit(limit).all()

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 

def update_user(db: Session, user_id: int, user: user_schema.UserUpdate):
    """
    更新用户信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        user: 包含用户更新信息的模型
        
    Returns:
        User: 更新后的用户对象
        
    Raises:
        HTTPException: 如果用户不存在则抛出404错误
    """
    # 查找用户
    db_user = get_user(db, user_id=user_id)
    
    # 如果用户不存在，抛出404错误
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新用户信息
    if user.username is not None:
        # 检查用户名是否已被使用
        existing_user = get_user_by_username(db, username=user.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Username already registered")
        db_user.username = user.username
        
    if user.email is not None:
        # 检查邮箱是否已被使用
        existing_user = get_user_by_email(db, email=user.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user.email
        
    if user.password is not None:
        db_user.hashed_password = get_password_hash(user.password)
    
    # 提交更改
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def delete_user(db: Session, user_id: int):
    """
    软删除用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果用户不存在则抛出404错误
    """
    # 查找用户
    db_user = db.query(User).filter(User.id == user_id).first()
    
    # 如果用户不存在，抛出404错误
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 执行软删除
    db_user.is_deleted = True
    db_user.deleted_at = datetime.now()
    
    # 提交更改
    db.add(db_user)
    db.commit()
    
    return {"message": f"User {db_user.username} has been deleted"}

def restore_user(db: Session, user_id: int):
    """
    恢复已删除的用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果用户不存在则抛出404错误，如果用户未被删除则抛出400错误
    """
    # 查找用户，包括已删除的用户
    db_user = db.query(User).filter(User.id == user_id).first()
    
    # 如果用户不存在，抛出404错误
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 如果用户未被删除，抛出400错误
    if not db_user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not deleted")
    
    # 恢复用户
    db_user.is_deleted = False
    db_user.deleted_at = None
    
    # 提交更改
    db.add(db_user)
    db.commit()
    
    return {"message": f"User {db_user.username} has been restored"}

def get_user_profile(db: Session, user_id: int):
    """
    获取用户详细资料，包括帖子数、评论数等统计信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Dict: 包含用户详细资料的字典
        
    Raises:
        HTTPException: 如果用户不存在则抛出404错误
    """
    # 查找用户
    db_user = get_user(db, user_id=user_id)
    
    # 如果用户不存在，抛出404错误
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取用户的帖子数量
    post_count = db.query(Post).filter(
        Post.author_id == user_id,
        Post.is_deleted == False
    ).count()
    
    # 获取用户的评论数量（假设有Comment表）
    comment_count = 0
    try:
        from ..db.models import Comment
        comment_count = db.query(Comment).filter(
            Comment.author_id == user_id,
            Comment.is_deleted == False
        ).count()
    except:
        # 如果Comment表不存在，忽略错误
        pass
    
    # 创建用户资料对象
    user_profile = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "bio": db_user.bio if hasattr(db_user, 'bio') else None,
        "avatar_url": db_user.avatar_url if hasattr(db_user, 'avatar_url') else None,
        "is_active": db_user.is_active,
        "role": db_user.role,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at if hasattr(db_user, 'updated_at') else db_user.created_at,
        "post_count": post_count,
        "comment_count": comment_count,
        "last_login": db_user.last_login if hasattr(db_user, 'last_login') else None,
        "join_date": db_user.created_at,
        "reputation": db_user.reputation if hasattr(db_user, 'reputation') else 0,
        "badges": db_user.badges if hasattr(db_user, 'badges') else []
    }
    
    return user_profile

def get_user_posts(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    """
    获取用户发布的所有帖子
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 分页偏移量
        limit: 每页数量
        
    Returns:
        List[Post]: 用户帖子列表
    """
    posts = db.query(Post).filter(
        Post.author_id == user_id,
        Post.is_deleted == False
    ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    return posts 