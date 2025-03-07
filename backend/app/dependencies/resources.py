from fastapi import Path, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..db.models import User, Post, Comment, Section, Category
from .auth import get_current_user

async def get_db_from_request(request):
    """从请求中获取数据库会话
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Session: SQLAlchemy数据库会话
    """
    return request.state.db

async def get_post_or_404(
    post_id: int = Path(..., description="帖子ID"),
    db: Session = Depends(get_db_from_request)
):
    """获取帖子或返回404
    
    Args:
        post_id: 帖子ID
        db: 数据库会话
        
    Returns:
        Post: 帖子对象
        
    Raises:
        HTTPException: 如果帖子不存在，则抛出404异常
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    return post

async def get_section_or_404(
    section_id: int = Path(..., description="版块ID"),
    db: Session = Depends(get_db_from_request)
):
    """获取版块或返回404
    
    Args:
        section_id: 版块ID
        db: 数据库会话
        
    Returns:
        Section: 版块对象
        
    Raises:
        HTTPException: 如果版块不存在，则抛出404异常
    """
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=404,
            detail="版块不存在"
        )
    return section

async def get_category_or_404(
    category_id: int = Path(..., description="分类ID"),
    db: Session = Depends(get_db_from_request)
):
    """获取分类或返回404
    
    Args:
        category_id: 分类ID
        db: 数据库会话
        
    Returns:
        Category: 分类对象
        
    Raises:
        HTTPException: 如果分类不存在，则抛出404异常
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail="分类不存在"
        )
    return category

async def get_comment_or_404(
    comment_id: int = Path(..., description="评论ID"),
    db: Session = Depends(get_db_from_request)
):
    """获取评论或返回404
    
    Args:
        comment_id: 评论ID
        db: 数据库会话
        
    Returns:
        Comment: 评论对象
        
    Raises:
        HTTPException: 如果评论不存在，则抛出404异常
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="评论不存在"
        )
    return comment

async def validate_post_access(
    post: Post = Depends(get_post_or_404),
    current_user: Optional[User] = Depends(get_current_user)
):
    """验证用户是否可以访问指定帖子
    
    Args:
        post: 帖子对象
        current_user: 当前用户对象
        
    Returns:
        Post: 帖子对象
        
    Raises:
        HTTPException: 如果用户无权访问，则抛出403异常
    """
    # 检查帖子是否是私密的
    if getattr(post, "is_private", False):
        # 未登录用户无法查看私密帖子
        if not current_user:
            raise HTTPException(
                status_code=403,
                detail="没有权限访问该帖子"
            )
        
        # 只有作者和管理员可以查看私密帖子
        is_admin = getattr(current_user, "is_admin", False)
        if current_user.id != post.author_id and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="没有权限访问该帖子"
            )
    
    return post 