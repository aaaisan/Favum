"""
用户数据访问仓储

提供对User实体的异步数据库操作封装，扩展基础Repository。
主要功能：
- 基本CRUD操作（继承自BaseRepository）
- 用户特定查询方法（如通过email查询）
- 支持软删除和恢复
"""

from sqlalchemy import select, and_, or_, func, update
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .base_repository import BaseRepository
from ..models import User, Post, Comment

class UserRepository(BaseRepository):
    """User实体的数据访问仓储类"""
    
    def __init__(self):
        """初始化用户仓储
        
        设置模型类型为User
        """
        super().__init__(User)
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """通过邮箱查询用户
        
        Args:
            email: 用户邮箱地址
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        query = select(self.model).where(
            and_(
                self.model.email == email,
                self.model.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        return item.to_dict() if item else None
    
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """通过用户名查询用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        query = select(self.model).where(
            and_(
                self.model.username == username,
                self.model.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        return item.to_dict() if item else None
    
    async def get_user_posts(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户发布的帖子
        
        Args:
            user_id: 用户ID
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        # 查询帖子
        query = select(Post).where(
            and_(
                Post.author_id == user_id,
                Post.is_deleted == False
            )
        ).order_by(Post.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        posts = [post.to_dict() for post in result.scalars().all()]
        
        # 查询总数
        count_query = select(func.count()).where(
            and_(
                Post.author_id == user_id,
                Post.is_deleted == False
            )
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        return posts, total
        
    async def soft_delete(self, user_id: int) -> bool:
        """软删除用户
        
        将用户标记为已删除状态，而不是物理删除
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        # 构建更新语句
        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        
        # 执行更新
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # 检查是否找到并更新了记录
        return result.rowcount > 0
    
    async def restore(self, user_id: int) -> bool:
        """恢复软删除的用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        async with self.db.begin() as session:
            update_stmt = update(self.model).where(
                self.model.id == user_id
            ).values(
                is_deleted=False,
                updated_at=datetime.utcnow()
            )
            result = await session.execute(update_stmt)
            
            return result.rowcount > 0
            
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详细资料，包括帖子数、评论数等统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 包含用户详细资料的字典，不存在则返回None
        """
        # 查找用户
        user = await self.get_by_id(user_id)
        
        # 如果用户不存在，返回None
        if not user:
            return None
        
        # 获取用户的帖子数量
        async with self.db.begin() as session:
            # 获取用户的帖子数量
            post_count_query = select(func.count()).select_from(Post).where(
                and_(
                    Post.author_id == user_id,
                    Post.is_deleted == False
                )
            )
            post_count_result = await session.execute(post_count_query)
            post_count = post_count_result.scalar() or 0
            
            # 获取用户的评论数量
            comment_count_query = select(func.count()).select_from(Comment).where(
                and_(
                    Comment.author_id == user_id,
                    Comment.is_deleted == False
                )
            )
            
            comment_count_result = await session.execute(comment_count_query)
            comment_count = comment_count_result.scalar() or 0
        
        # 创建用户资料对象
        user_profile = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "bio": user.get("bio"),
            "avatar_url": user.get("avatar_url"),
            "is_active": user["is_active"],
            "role": user["role"],
            "created_at": user["created_at"],
            "updated_at": user.get("updated_at", user["created_at"]),
            "post_count": post_count,
            "comment_count": comment_count,
            "last_login": user.get("last_login"),
            "join_date": user["created_at"],
            "reputation": user.get("reputation", 0),
            "badges": user.get("badges", [])
        }
        
        return user_profile 