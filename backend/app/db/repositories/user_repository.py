"""
用户数据访问仓储

提供对User实体的异步数据库操作封装，扩展基础Repository。
主要功能：
- 基本CRUD操作（继承自BaseRepository）
- 用户特定查询方法（如通过email查询）
- 支持软删除和恢复
"""

from sqlalchemy import select, and_, func, update
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import redis
from ...core.config import settings
from ...core.redis import redis_client

from .base_repository import BaseRepository
from ..models import User, Post, Comment, PostFavorite
from ...schemas.responses.user import (
    UserResponse,
    UserProfileResponse,
    UserInfoResponse,
    UserListResponse
)
from ...schemas.responses.post import PostListResponse
# from ...core.database import async_get_db, AsyncSessionLocal
from ...core.database import async_get_db
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User, UserResponse]):
    """User实体的数据访问仓储类"""
    
    def __init__(self):
        """初始化用户仓储
        
        设置模型类型为User
        """
        super().__init__(User, UserResponse)
    
    # 重写model_to_dict方法，排除敏感字段
    def model_to_dict(self, model) -> Dict[str, Any]:
        """将用户模型对象转换为字典，排除敏感字段
        
        Args:
            model: 用户模型对象
            
        Returns:
            Dict[str, Any]: 不包含敏感信息的字典
        """
        result = super().model_to_dict(model)
        
        # 从结果中移除敏感字段
        sensitive_fields = "hashed_password"
        if hasattr(result, sensitive_fields):
            del result[sensitive_fields]
                
        return result
    
    async def get_user_post_count(self, user_id: int) -> int:
        """获取用户的帖子数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 用户帖子的总数量
        """
        async with self.async_get_db() as db:
            count_query = select(func.count()).select_from(Post).where(
                and_(
                    Post.author_id == user_id,
                    Post.is_deleted == False
                )
            )
            try:
                count_result = await db.execute(count_query)
                return count_result.scalar() or 0
            except Exception as e:
                logger.error(f"获取帖子数量失败: {str(e)}")
                return 0
                
    async def get_user_comment_count(self, user_id: int) -> int:
        """获取用户的评论数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 用户评论的总数量
        """
        async with self.async_get_db() as db:
            count_query = select(func.count()).select_from(Comment).where(
                and_(
                    Comment.author_id == user_id,
                    Comment.is_deleted == False
                )
            )
            try:
                comment_count_result = await db.execute(count_query)
                return comment_count_result.scalar() or 0
            except Exception as e:
                logger.error(f"获取评论数量失败: {str(e)}")
                return 0
    
    async def get_by_username(self, username: str) -> Optional[UserResponse]:
        """通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[UserResponse]: 用户对象，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                result = await db.execute(
                    select(User).where(
                        (User.username == username) &
                        (User.is_deleted == False)
                    )
                )
                user = result.scalar_one_or_none()
                return self.to_schema(user)
            except Exception as e:
                logger.error(f"获取用户失败: {str(e)}")
                return None
    
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        """通过邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            Optional[UserResponse]: 用户对象，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                result = await db.execute(
                    select(User).where(
                        (User.email == email) &
                        (User.is_deleted == False)
                    )
                )
                user = result.scalar_one_or_none()
                return self.to_schema(user)
            except Exception as e:
                logger.error(f"获取用户失败: {str(e)}")
                return None
    
    async def get_user_posts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        # TODO: 改为返回PostResponse对象列表
        async with async_get_db() as db:
            try:
                # 获取帖子
                query = select(Post).where(
                    (Post.author_id == user_id) &
                    (Post.is_deleted == False)
                ).order_by(Post.created_at.desc()).offset(skip).limit(limit)
                
                result = await db.execute(query)
                posts = result.scalars().all()
                
                # 获取总数
                count_query = select(func.count()).select_from(Post).where(
                    (Post.author_id == user_id) &
                    (Post.is_deleted == False)
                )
                
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
                
                # 转换为字典列表
                post_dicts = []
                for post in posts:
                    post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                    post_dicts.append(post_dict)
                
                return post_dicts, total
            except Exception as e:
                logger.error(f"获取用户帖子失败: {str(e)}")
                return [], 0
    
    async def get_user_comments(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的评论列表
        
        Args:
            user_id: 用户ID
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 评论列表和总数
        """
        # TODO: 改为返回CommentResponse对象列表
        async with async_get_db() as db:
            try:
                # 获取评论
                query = select(Comment).where(
                    (Comment.author_id == user_id) &
                    (Comment.is_deleted == False)
                ).order_by(Comment.created_at.desc()).offset(skip).limit(limit)
                
                result = await db.execute(query)
                comments = result.scalars().all()
                
                # 获取总数
                count_query = select(func.count()).select_from(Comment).where(
                    (Comment.author_id == user_id) &
                    (Comment.is_deleted == False)
                )
                
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
                
                # 转换为字典列表
                comment_dicts = []
                for comment in comments:
                    comment_obj = self.to_schema(comment)
                    # comment_dict = {c.name: getattr(comment, c.name) for c in comment.__table__.columns}
                    comment_dicts.append(comment_obj)
                
                return comment_dicts, total
            except Exception as e:
                logger.error(f"获取用户评论失败: {str(e)}")
                return [], 0
    
    async def get_user_favorites(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户的收藏帖子列表
        
        Args:
            user_id: 用户ID
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 收藏帖子列表和总数
        """
        # TODO: 改为返回PostResponse对象列表
        async with async_get_db() as db:
            try:
                # 获取收藏的帖子ID
                join_query = select(PostFavorite.post_id).where(
                    (PostFavorite.user_id == user_id) &
                    (PostFavorite.is_deleted == False)
                )
                
                # 获取帖子
                query = select(Post).where(
                    (Post.id.in_(join_query)) &
                    (Post.is_deleted == False)
                ).order_by(Post.created_at.desc()).offset(skip).limit(limit)
                
                result = await db.execute(query)
                posts = result.scalars().all()
                
                # 获取总数
                count_query = select(func.count()).select_from(Post).where(
                    (Post.id.in_(join_query)) &
                    (Post.is_deleted == False)
                )
                
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
                
                # 转换为字典列表
                post_dicts = []
                for post in posts:
                    post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                    post_dicts.append(post_dict)
                
                return post_dicts, total
            except Exception as e:
                logger.error(f"获取用户收藏失败: {str(e)}")
                return [], 0

    async def set_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功更新
        """
        async with async_get_db() as db:
            try:
                # 获取要更新的用户
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # 更新最后登录时间
                user.last_login = datetime.now()
                await db.commit()
                return True
            except Exception as e:
                await db.rollback()
                logger.error(f"更新最后登录时间失败: {str(e)}")
                return False
    
    async def increase_login_count(self, user_id: int) -> bool:
        """增加用户登录次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功更新
        """
        async with async_get_db() as db:
            try:
                # 获取要更新的用户
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # 增加登录次数
                user.login_count = (user.login_count or 0) + 1
                await db.commit()
                return True
            except Exception as e:
                await db.rollback()
                logger.error(f"增加登录次数失败: {str(e)}")
                return False
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfileResponse]:
        """获取用户详细资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfileResponse]: 用户详细资料响应对象，不存在则返回None
        """
        # 获取基本用户信息
        user = await self.get(user_id)
        if not user:
            return None
            
        # 获取统计信息
        post_count = await self.get_user_post_count(user_id)
        comment_count = await self.get_user_comment_count(user_id)
        
        # 构建用户资料
        return UserProfileResponse(
            **user.model_dump(),
            post_count=post_count,
            comment_count=comment_count,
            join_date=user.created_at
        )
    
    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """通过ID查询用户
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的用户
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        async with self.async_get_db() as db:
        # session = await self.get_session()
        # try:
            # 构建查询条件
            conditions = [self.model.id == user_id]
            if not include_deleted:
                conditions.append(self.model.is_deleted == False)
                
            query = select(self.model).where(and_(*conditions))
            try:
                result = await db.execute(query)
                user = result.scalar_one_or_none()
                return self.model_to_dict(user)
            except Exception as e:
                logger.error(f"获取用户失败: {str(e)}")
                return None
    
    async def set_verification_token(self, email: str, token: str, expires: int = 3600) -> bool:
        """存储邮箱验证令牌到Redis
        
        Args:
            email: 用户邮箱
            token: 验证令牌
            expires: 过期时间（秒），默认1小时
            
        Returns:
            bool: 操作是否成功
        """
        key = f"email_verification:{email}"
        try:
            redis_client.setex(key, expires, token)
            return True
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"存储验证令牌失败: {str(e)}")
            return False
    
    async def get_verification_token(self, email: str) -> Optional[str]:
        """从Redis获取邮箱验证令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            Optional[str]: 验证令牌，不存在则返回None
        """
        key = f"email_verification:{email}"
        try:
            token = redis_client.get(key)
            return token
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"获取验证令牌失败: {str(e)}")
            return None
    
    async def delete_verification_token(self, email: str) -> bool:
        """从Redis删除邮箱验证令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            bool: 操作是否成功
        """
        key = f"email_verification:{email}"
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"删除验证令牌失败: {str(e)}")
            return False
    
    async def set_reset_token(self, email: str, token: str, expires: int = 3600) -> bool:
        """存储密码重置令牌到Redis
        
        Args:
            email: 用户邮箱
            token: 重置令牌
            expires: 过期时间（秒），默认1小时
            
        Returns:
            bool: 操作是否成功
        """
        email_key = f"password_reset:{email}"
        token_key = f"token:password_reset:{token}"
        try:
            # 存储两条记录，便于双向查找
            # 1. email -> token 映射
            redis_client.setex(email_key, expires, token)
            # 2. token -> email 映射
            redis_client.setex(token_key, expires, email)
            return True
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"存储重置令牌失败: {str(e)}")
            return False
    
    async def get_reset_token(self, email: str) -> Optional[str]:
        """从Redis获取与邮箱关联的密码重置令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            Optional[str]: 重置令牌，不存在则返回None
        """
        key = f"password_reset:{email}"
        try:
            token = redis_client.get(key)
            return token
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"获取重置令牌失败: {str(e)}")
            return None
    
    async def get_email_by_reset_token(self, token: str) -> Optional[str]:
        """从Redis获取与令牌关联的邮箱
        
        Args:
            token: 重置令牌
            
        Returns:
            Optional[str]: 关联的邮箱，不存在则返回None
        """
        key = f"token:password_reset:{token}"
        try:
            email = redis_client.get(key)
            return email
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"通过令牌获取邮箱失败: {str(e)}")
            return None
    
    async def delete_reset_token(self, email: str, token: str = None) -> bool:
        """从Redis删除密码重置令牌
        
        Args:
            email: 用户邮箱
            token: 重置令牌(可选)，如果提供则同时删除token->email映射
            
        Returns:
            bool: 操作是否成功
        """
        email_key = f"password_reset:{email}"
        try:
            # 如果没有提供token，先尝试获取
            if not token:
                token = redis_client.get(email_key)
            
            # 删除email->token映射
            redis_client.delete(email_key)
            
            # 如果有token，删除token->email映射
            if token:
                token_key = f"token:password_reset:{token}"
                redis_client.delete(token_key)
                
            return True
        except Exception as e:
            # 此处应该记录日志
            logger.error(f"删除重置令牌失败: {str(e)}")
            return False
    
    async def get_user_post_ids(self, user_id: int, limit: int = 10) -> List[int]:
        """获取用户发布的帖子ID列表
        
        Args:
            user_id: 用户ID
            limit: 限制返回数量，默认为10
            
        Returns:
            List[int]: 帖子ID列表
        """
        async with self.async_get_db() as db:
            query = select(Post.id).where(
                and_(
                    Post.author_id == user_id,
                    Post.is_deleted == False
                )
            ).order_by(Post.created_at.desc()).limit(limit)
            
            try:
                result = await db.execute(query)
                return [post_id for post_id in result.scalars().all()]
            except Exception as e:
                logger.error(f"获取用户帖子ID列表失败: {str(e)}")
                return []
    
    async def get_user_favorite_post_ids(self, user_id: int, limit: int = 10) -> List[int]:
        """获取用户收藏的帖子ID列表
        
        Args:
            user_id: 用户ID
            limit: 限制返回数量，默认为10
            
        Returns:
            List[int]: 收藏的帖子ID列表
        """
        async with self.async_get_db() as db:
            query = select(PostFavorite.post_id).where(
                PostFavorite.user_id == user_id
            ).order_by(PostFavorite.created_at.desc()).limit(limit)
            
            try:
                result = await db.execute(query)
                return [post_id for post_id in result.scalars().all()]
            except Exception as e:
                logger.error(f"获取用户收藏帖子ID列表失败: {str(e)}")
                return []
    
    async def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[UserProfileResponse]:
        """更新用户资料
        
        Args:
            user_id: 用户ID
            profile_data: 资料数据字典
            
        Returns:
            Optional[UserProfileResponse]: 更新后的用户资料，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                # 获取要更新的用户
                result = await db.execute(
                    select(User).where(
                        (User.id == user_id) &
                        (User.is_deleted == False)
                    )
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                
                # 更新资料字段
                for key, value in profile_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                user.updated_at = datetime.now()
                await db.commit()
                await db.refresh(user)
                
                # 将用户对象转换为字典
                user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
                
                # 创建并返回UserProfileResponse对象
                return UserProfileResponse(**user_dict)
            except Exception as e:
                await db.rollback()
                logger.error(f"更新用户资料失败: {str(e)}")
                return None
    
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
        async with self.async_get_db() as db:
            try:
                result = await db.execute(stmt)
                await db.commit()
            except Exception as e:
                logger.error(f"软删除用户失败: {str(e)}")
                return False
        
        # 检查是否找到并更新了记录
        # return result.rowcount > 0
        return True
    
    async def restore(self, user_id: int) -> bool:
        """恢复软删除的用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        async with self.async_get_db() as db:
            update_stmt = update(self.model).where(
                self.model.id == user_id
            ).values(
                is_deleted=False,
                updated_at=datetime.now()
            )
            try:
                result = await db.execute(update_stmt)
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"恢复用户失败: {str(e)}")
                return False
    
    async def get_user_favorite_post_ids(self, user_id: int, limit: int = 10) -> List[int]:
        """获取用户收藏的帖子ID列表
        
        Args:
            user_id: 用户ID
            limit: 限制返回数量，默认为10
            
        Returns:
            List[int]: 收藏的帖子ID列表
        """
        async with self.async_get_db() as db:
            query = select(PostFavorite.post_id).where(
                PostFavorite.user_id == user_id
            ).order_by(PostFavorite.created_at.desc()).limit(limit)
            
            try:
                result = await db.execute(query)
                return [post_id for post_id in result.scalars().all()]
            except Exception as e:
                logger.error(f"获取用户收藏帖子ID列表失败: {str(e)}")
                return [] 