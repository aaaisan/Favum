from fastapi import Depends, HTTPException
from ..db.models import User, Post, Section, SectionModerator
from sqlalchemy.orm import Session
from typing import Optional
from .auth import get_current_user, require_user

async def require_admin(current_user: User = Depends(require_user)):
    """要求用户拥有管理员权限
    
    Args:
        current_user: 已认证的用户对象
        
    Returns:
        User: 具有管理员权限的用户对象
        
    Raises:
        HTTPException: 如果用户不是管理员，则抛出403异常
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return current_user

async def is_section_moderator(user_id: int, section_id: int, db: Session) -> bool:
    """检查用户是否为指定版块的版主
    
    Args:
        user_id: 用户ID
        section_id: 版块ID
        db: 数据库会话
        
    Returns:
        bool: 如果用户是版主则返回True，否则返回False
    """
    # 查询用户是否是该版块的版主
    moderator = db.query(SectionModerator).filter(
        SectionModerator.user_id == user_id,
        SectionModerator.section_id == section_id
    ).first()
    
    return moderator is not None

async def require_moderator(
    section_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(lambda request: request.state.db)
):
    """要求用户是指定版块的版主或管理员
    
    Args:
        section_id: 版块ID
        current_user: 已认证的用户对象
        db: 数据库会话
        
    Returns:
        User: 具有版主或管理员权限的用户对象
        
    Raises:
        HTTPException: 如果用户不是版主或管理员，则抛出403异常
    """
    # 管理员自动拥有所有权限
    if getattr(current_user, "is_admin", False):
        return current_user
    
    # 检查用户是否是指定版块的版主
    is_mod = await is_section_moderator(current_user.id, section_id, db)
    if not is_mod:
        raise HTTPException(
            status_code=403,
            detail="需要版主或管理员权限"
        )
    
    return current_user

async def check_post_ownership(
    post_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(lambda request: request.state.db)
):
    """检查用户是否是帖子的作者
    
    Args:
        post_id: 帖子ID
        current_user: 已认证的用户对象
        db: 数据库会话
        
    Returns:
        Post: 帖子对象
        
    Raises:
        HTTPException: 如果帖子不存在或用户不是作者，则抛出相应异常
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    if post.author_id != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="无权操作此帖子"
        )
    
    return post 