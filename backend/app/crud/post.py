from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..db.models import Post, Tag, post_tags, PostVote, VoteType
from ..schemas import post as post_schema
import sqlalchemy.orm
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100, include_hidden: bool = False):
    """获取帖子列表
    
    默认不返回已隐藏的帖子
    
    Args:
        db: 数据库会话
        skip: 跳过数量
        limit: 返回数量限制
        include_hidden: 是否包含隐藏的帖子
        
    Returns:
        List[Post]: 帖子列表
    """
    query = db.query(Post)
    if not include_hidden:
        query = query.filter(Post.is_hidden == False)
    return query.offset(skip).limit(limit).all()

def get_public_post(db: Session, post_id: int):
    """获取单个公开帖子，带有关联的分类信息
    
    为游客访问优化，不加载敏感信息，且不返回隐藏的帖子
    """
    return db.query(Post).options(
        sqlalchemy.orm.joinedload(Post.category),
        sqlalchemy.orm.joinedload(Post.section)
    ).filter(Post.id == post_id, Post.is_hidden == False).first()

def get_public_posts(db: Session, skip: int = 0, limit: int = 100):
    """获取公开帖子列表，带有关联的分类信息
    
    为游客访问优化，不加载敏感信息，且不返回隐藏的帖子
    """
    return db.query(Post).options(
        sqlalchemy.orm.joinedload(Post.category),
        sqlalchemy.orm.joinedload(Post.section)
    ).filter(Post.is_hidden == False).offset(skip).limit(limit).all()

def create_post(db: Session, post: post_schema.PostCreate):
    # 排除tag_ids字段，因为Post模型不接受这个参数
    post_data = post.model_dump()
    if 'tag_ids' in post_data:
        tag_ids = post_data.pop('tag_ids')
        print(f"已移除tag_ids: {tag_ids}")  # 添加调试信息
    
    db_post = Post(**post_data)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_post(db: Session, post_id: int, post: post_schema.PostUpdate):
    db_post = get_post(db, post_id)
    update_data = post.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 使用软删除代替物理删除
    db_post.is_deleted = True
    
    # 如果有deleted_at字段，设置删除时间
    if hasattr(db_post, "deleted_at"):
        db_post.deleted_at = datetime.now()
    
    db.add(db_post)
    db.commit()
    return {"detail": "帖子已删除"}

def restore_post(db: Session, post_id: int):
    """恢复已删除的帖子
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        
    Returns:
        dict: 包含操作结果的消息
        
    Raises:
        HTTPException: 如果帖子不存在则抛出404错误，如果帖子未被删除则抛出400错误
    """
    # 查找帖子，包括已删除的
    db_post = db.query(Post).filter(Post.id == post_id).first()
    
    # 如果帖子不存在，抛出404错误
    if not db_post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 如果帖子未被删除，抛出400错误
    if not db_post.is_deleted:
        raise HTTPException(status_code=400, detail="帖子未被删除")
    
    # 恢复帖子
    db_post.is_deleted = False
    db_post.deleted_at = None
    
    # 提交更改
    db.add(db_post)
    db.commit()
    
    return {"detail": "帖子已恢复"}

def toggle_post_hidden(db: Session, post_id: int, hidden: bool):
    """切换帖子隐藏状态
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        hidden: 是否隐藏
        
    Returns:
        Post: 更新后的帖子
    """
    db_post = get_post(db, post_id)
    if db_post:
        db_post.is_hidden = hidden
        db.commit()
        db.refresh(db_post)
    return db_post

# 添加点赞相关的CRUD操作
def get_user_vote(db: Session, post_id: int, user_id: int):
    """获取用户对指定帖子的点赞状态
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        user_id: 用户ID
        
    Returns:
        PostVote: 点赞记录，若不存在则返回None
    """
    return db.query(PostVote).filter(
        PostVote.post_id == post_id,
        PostVote.user_id == user_id
    ).first()

def vote_post(db: Session, post_id: int, user_id: int, vote_type: str):
    """用户对帖子进行点赞或反对
    
    核心逻辑：
    - 用户点赞：vote_count += 1
    - 用户反对：vote_count -= 1 
    - 取消点赞：vote_count -= 1
    - 取消反对：vote_count += 1
    - 从点赞改为反对：vote_count -= 2 (撤销点赞 -1 然后反对 -1)
    - 从反对改为点赞：vote_count += 2 (撤销反对 +1 然后点赞 +1)
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        user_id: 用户ID
        vote_type: 点赞类型(upvote/downvote)
        
    Returns:
        dict: 包含点赞结果和更新后的帖子点赞数
        
    Raises:
        HTTPException: 如果帖子不存在则抛出404错误
    """
    # 检查帖子是否存在
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查用户是否已经对这个帖子进行过点赞或反对
    existing_vote = get_user_vote(db, post_id, user_id)
    
    # 计算点赞的影响
    vote_impact = 0
    
    if existing_vote:
        # 如果用户已经对此帖子投票，则检查是否是相同类型的投票
        if existing_vote.vote_type == vote_type:
            # 相同类型的投票，取消投票
            db.delete(existing_vote)
            # 根据取消的投票类型调整影响值
            # 取消点赞：-1，取消反对：+1
            vote_impact = -1 if vote_type == VoteType.UPVOTE else 1
            message = "取消点赞" if vote_type == VoteType.UPVOTE else "取消反对"
        else:
            # 不同类型的投票，更新为新的投票类型
            existing_vote.vote_type = vote_type
            db.add(existing_vote)
            # 从旧的投票类型转换到新的投票类型，影响是两倍
            # 从反对改为点赞：+2，从点赞改为反对：-2
            vote_impact = 2 if vote_type == VoteType.UPVOTE else -2
            message = "从反对改为点赞" if vote_type == VoteType.UPVOTE else "从点赞改为反对"
    else:
        # 如果用户还没有对此帖子投票，则创建新的投票记录
        db_vote = PostVote(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_type
        )
        db.add(db_vote)
        # 新的投票的影响
        # 新点赞：+1，新反对：-1
        vote_impact = 1 if vote_type == VoteType.UPVOTE else -1
        message = "点赞成功" if vote_type == VoteType.UPVOTE else "反对成功"
    
    # 更新帖子的点赞数
    db_post.vote_count += vote_impact
    db.add(db_post)
    
    try:
        db.commit()
        db.refresh(db_post)
        return {
            "success": True,
            "vote_count": db_post.vote_count,
            "message": message
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="操作失败，请稍后重试")

def get_post_votes(db: Session, post_id: int):
    """获取帖子的点赞数量
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        
    Returns:
        int: 帖子点赞数
    """
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post.vote_count 