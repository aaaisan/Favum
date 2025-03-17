from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc
# from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from ..models.comment import Comment
from ..models.user import User
from .base_repository import BaseRepository
from ...schemas.responses.comment import CommentDetailResponse

class CommentRepository(BaseRepository):
    """评论仓库
    
    提供评论相关的数据库访问方法，包括查询、创建、更新和删除评论。
    """
    
    def __init__(self):
        """初始化评论仓库"""
        super().__init__(Comment)
    
    async def get_by_id(self, comment_id: int, include_deleted: bool = False) -> Optional[CommentDetailResponse]:
        """根据ID获取评论
        
        Args:
            comment_id: 评论ID
            include_deleted: 是否包含已删除的评论
            
        Returns:
            Optional[CommentDetailResponse]: 评论信息对象，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = (
                select(Comment, User.username.label("author_name"))
                .join(User, Comment.author_id == User.id)
                .where(Comment.id == comment_id)
            )
            
            if not include_deleted:
                query = query.where(Comment.is_deleted == False)
                
            result = await db.execute(query)
            row = result.first()
            
            if row is None:
                return None
                
            comment, author_name = row
            
            # 将模型实例转换为schema对象
            comment_schema = self.to_schema(comment)
            comment_schema.author_name = author_name
            
            return comment_schema
            
    async def get_comments_by_post(
        self, 
        post_id: int, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[CommentDetailResponse], int]:
        """获取帖子下的评论列表
        
        Args:
            post_id: 帖子ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_deleted: 是否包含已删除的评论
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 评论列表和总数
        """
        async with self.async_get_db() as db:
            # 查询条件
            conditions = [Comment.post_id == post_id]
            if not include_deleted:
                conditions.append(Comment.is_deleted == False)
            
            # 查询评论数据
            query = (
                select(Comment, User.username.label("author_name"))
                .join(User, Comment.author_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(Comment.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            
            # 查询总数
            count_query = select(func.count(Comment.id)).where(and_(*conditions))
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            comments = []
            for row in result:
                comment, author_name = row
                comment_schema = self.to_schema(comment)
                comment_schema.author_name = author_name
                comments.append(comment_schema)
                
            return comments, total
    
    async def create(self, comment_data: Dict[str, Any]) -> CommentDetailResponse:
        """创建新评论
        
        Args:
            comment_data: 评论数据
            
        Returns:
            Dict[str, Any]: 创建的评论
        """
        async with self.async_get_db() as db:
            # 创建新评论
            comment = Comment(**comment_data)
            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            
            # 获取作者信息
            user_query = select(User.username).where(User.id == comment.author_id)
            result = await db.execute(user_query)
            author_name = result.scalar_one_or_none()
            
            # 返回评论字典
            comment_schema = self.to_schema(comment)
            comment_schema.author_name = author_name
            
            return comment_schema
            
    async def update(self, comment_id: int, data: Dict[str, Any]) -> Optional[CommentDetailResponse]:
        """更新评论
        
        Args:
            comment_id: 评论ID
            data: 要更新的数据
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的评论，不存在则返回None
        """
        async with self.async_get_db() as db:
            # 查询评论是否存在
            comment = await db.get(Comment, comment_id)
            if not comment or comment.is_deleted:
                return None
                
            # 更新评论
            for key, value in data.items():
                if hasattr(comment, key):
                    setattr(comment, key, value)
            
            await db.commit()
            await db.refresh(comment)
            
            # 获取作者信息
            user_query = select(User.username).where(User.id == comment.author_id)
            result = await db.execute(user_query)
            author_name = result.scalar_one_or_none()
            
            # 返回评论字典
            comment_schema = self.to_schema(comment)
            comment_schema.author_name = author_name
            
            return comment_schema
            
    async def soft_delete(self, comment_id: int) -> bool:
        """软删除评论
        
        Args:
            comment_id: 评论ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 查询评论是否存在
            comment = await db.get(Comment, comment_id)
            if not comment or comment.is_deleted:
                return False
                
            # 软删除评论
            comment.is_deleted = True
            comment.deleted_at = datetime.now()
            
            await db.commit()
            return True
            
    async def restore(self, comment_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的评论
        
        Args:
            comment_id: 评论ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的评论，如果评论不存在或未被删除则返回None
        """
        async with self.async_get_db() as db:
            # 查询评论是否存在
            comment = await db.get(Comment, comment_id)
            if not comment:
                return None
                
            # 如果评论未被删除，则无需恢复
            if not comment.is_deleted:
                return None
                
            # 恢复评论
            comment.is_deleted = False
            comment.deleted_at = None
            
            await db.commit()
            await db.refresh(comment)
            
            # 获取作者信息
            user_query = select(User.username).where(User.id == comment.author_id)
            result = await db.execute(user_query)
            author_name = result.scalar_one_or_none()
            
            # 返回评论字典
            comment_schema = self.to_schema(comment)
            comment_schema.author_name= author_name
            
            return comment_schema