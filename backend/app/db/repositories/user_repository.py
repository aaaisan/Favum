"""
用户数据访问仓储

提供对User实体的异步数据库操作封装，扩展基础Repository。
主要功能：
- 基本CRUD操作（继承自BaseRepository）
- 用户特定查询方法（如通过email查询）
- 支持软删除和恢复
"""

from sqlalchemy import select, and_, func, update
# from sqlalchemy import select, and_, func, update
# from sqlalchemy import select, and_, or_, func, update
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import redis
from ...core.config import settings

from .base_repository import BaseRepository
from ..models import User, Post, Comment
from ..database import async_get_db, AsyncSessionLocal
# from ..database import SessionLocal, async_get_db, AsyncSessionLocal
# from ..database import get_db, SessionLocal, AsyncSessionLocal
# from ..database import get_db, SessionLocal, async_get_db, AsyncSessionLocal

# 创建Redis连接
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True  # 自动将bytes解码为str
)

# Redis键前缀
VERIFICATION_TOKEN_PREFIX = "email_verification:"
RESET_TOKEN_PREFIX = "password_reset:"

class UserRepository(BaseRepository):
    """User实体的数据访问仓储类"""
    
    def __init__(self):
        """初始化用户仓储
        
        设置模型类型为User
        """
        super().__init__(User)
    
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
        sensitive_fields = ["hashed_password", "password_reset_token", "verification_token"]
        for field in sensitive_fields:
            if field in result:
                del result[field]
                
        return result
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """通过邮箱查询用户
        
        Args:
            email: 用户邮箱地址
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        
        async with async_get_db() as db:
            query = select(self.model).where(
                and_(
                    self.model.email == email,
                    self.model.is_deleted == False
                )
            )
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            return self.model_to_dict(user) if user else None
    
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """通过用户名查询用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        async with async_get_db() as db:
      
            query = select(self.model).where(
                and_(
                    self.model.username == username,
                    self.model.is_deleted == False
                )
            )
            try:
                result = await db.execute(query)
                user = result.scalar_one_or_none()
            except Exception as e:
                print(f"获取用户失败: {str(e)}")
                return None
            
            # if not item:
            #     return None
            # return type(item)
            # user_dict = self.model_to_dict(user) if user else None
            return self.model_to_dict(user) if user else None
            # return model_to_dict(user) if item else None
            # 返回一个简化的字典，只包含必要的字段
            # return {
            #     "id": item.id,
            #     "username": item.username,
            #     "email": item.email,
            #     "hashed_password": item.hashed_password,
            #     "is_active": item.is_active,
            #     "role": item.role
            # }
    
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
        # 获取数据库会话
        async with async_get_db() as db:
        
            # 查询帖子
            query = select(Post).where(
                and_(
                    Post.author_id == user_id,
                    Post.is_deleted == False
                )
            ).order_by(Post.created_at.desc()).offset(skip).limit(limit)
            try:
                result = await db.execute(query)
            except Exception as e:
                print(f"获取帖子失败: {str(e)}")
                return None
            posts = []
            try:
                for post in result.scalars().all():

                    posts.append(self.model_to_dict(post))
            except Exception as e:
                print(f"获取帖子失败: {str(e)}")
                return None
                # 手动处理帖子数据
                # post_data = {
                #     "id": post.id,
                #     "title": post.title,
                #     "content": post.content,
                #     "author_id": post.author_id,
                #     "created_at": post.created_at,
                #     "updated_at": post.updated_at,
                #     "is_hidden": post.is_hidden,
                #     "is_deleted": post.is_deleted,
                #     "category_id": post.category_id,
                #     "section_id": post.section_id
                # }
                # posts.append(post_data)
            
            # 查询总数
            try:
                count_query = select(func.count()).where(
                    and_(
                        Post.author_id == user_id,
                        Post.is_deleted == False
                    )
                )
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
            except Exception as e:
                print(f"获取帖子总数失败: {str(e)}")
                return None
            
            return posts, total
        # finally:
        #     await session.close()
        
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
        async with async_get_db() as db:
            try:
                result = await db.execute(stmt)
                await db.commit()
            except Exception as e:
                print(f"软删除用户失败: {str(e)}")
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
        async with async_get_db() as db:
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
                print(f"恢复用户失败: {str(e)}")
                return False
            
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户详细资料，包括帖子数、评论数等统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 包含用户详细资料的字典，不存在则返回None
        """
        # 查找用户
      
        user = await self.get_by_id(user_id)
        
        # 获取数据库会话
        async with async_get_db() as db:

            # 获取用户的帖子数量
            post_count_query = select(func.count()).select_from(Post).where(
                and_(
                    Post.author_id == user_id,
                    Post.is_deleted == False
                )
            )
            try:
                post_count_result = await db.execute(post_count_query)
                post_count = post_count_result.scalar() or 0
            except Exception as e:
                print(f"获取帖子数量失败: {str(e)}")
                return None
            
            # 获取用户的评论数量
            comment_count_query = select(func.count()).select_from(Comment).where(
                and_(
                    Comment.author_id == user_id,
                    Comment.is_deleted == False
                )
            )
            try:
                comment_count_result = await db.execute(comment_count_query)
                comment_count = comment_count_result.scalar() or 0
            except Exception as e:
                print(f"获取评论数量失败: {str(e)}")
                return None
        
            user_profile = self.model_to_dict(user)

            if post_count:
                user_profile["post_count"] = post_count
            if comment_count:
                user_profile["comment_count"] = comment_count

            return user_profile
    
    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """通过ID查询用户
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的用户
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据字典，不存在则返回None
        """
        async with async_get_db() as db:
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
                return self.model_to_dict(user) if user else None
            except Exception as e:
                print(f"获取用户失败: {str(e)}")
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
        key = f"{VERIFICATION_TOKEN_PREFIX}{email}"
        try:
            redis_client.setex(key, expires, token)
            return True
        except Exception as e:
            # 此处应该记录日志
            print(f"存储验证令牌失败: {str(e)}")
            return False
    
    async def get_verification_token(self, email: str) -> Optional[str]:
        """从Redis获取邮箱验证令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            Optional[str]: 验证令牌，不存在则返回None
        """
        key = f"{VERIFICATION_TOKEN_PREFIX}{email}"
        try:
            token = redis_client.get(key)
            return token
        except Exception as e:
            # 此处应该记录日志
            print(f"获取验证令牌失败: {str(e)}")
            return None
    
    async def delete_verification_token(self, email: str) -> bool:
        """从Redis删除邮箱验证令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            bool: 操作是否成功
        """
        key = f"{VERIFICATION_TOKEN_PREFIX}{email}"
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            # 此处应该记录日志
            print(f"删除验证令牌失败: {str(e)}")
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
        email_key = f"{RESET_TOKEN_PREFIX}{email}"
        token_key = f"token:{RESET_TOKEN_PREFIX}{token}"
        try:
            # 存储两条记录，便于双向查找
            # 1. email -> token 映射
            redis_client.setex(email_key, expires, token)
            # 2. token -> email 映射
            redis_client.setex(token_key, expires, email)
            return True
        except Exception as e:
            # 此处应该记录日志
            print(f"存储重置令牌失败: {str(e)}")
            return False
    
    async def get_reset_token(self, email: str) -> Optional[str]:
        """从Redis获取与邮箱关联的密码重置令牌
        
        Args:
            email: 用户邮箱
            
        Returns:
            Optional[str]: 重置令牌，不存在则返回None
        """
        key = f"{RESET_TOKEN_PREFIX}{email}"
        try:
            token = redis_client.get(key)
            return token
        except Exception as e:
            # 此处应该记录日志
            print(f"获取重置令牌失败: {str(e)}")
            return None
    
    async def get_email_by_reset_token(self, token: str) -> Optional[str]:
        """从Redis获取与令牌关联的邮箱
        
        Args:
            token: 重置令牌
            
        Returns:
            Optional[str]: 关联的邮箱，不存在则返回None
        """
        key = f"token:{RESET_TOKEN_PREFIX}{token}"
        try:
            email = redis_client.get(key)
            return email
        except Exception as e:
            # 此处应该记录日志
            print(f"通过令牌获取邮箱失败: {str(e)}")
            return None
    
    async def delete_reset_token(self, email: str, token: str = None) -> bool:
        """从Redis删除密码重置令牌
        
        Args:
            email: 用户邮箱
            token: 重置令牌(可选)，如果提供则同时删除token->email映射
            
        Returns:
            bool: 操作是否成功
        """
        email_key = f"{RESET_TOKEN_PREFIX}{email}"
        try:
            # 如果没有提供token，先尝试获取
            if not token:
                token = redis_client.get(email_key)
            
            # 删除email->token映射
            redis_client.delete(email_key)
            
            # 如果有token，删除token->email映射
            if token:
                token_key = f"token:{RESET_TOKEN_PREFIX}{token}"
                redis_client.delete(token_key)
                
            return True
        except Exception as e:
            # 此处应该记录日志
            print(f"删除重置令牌失败: {str(e)}")
            return False 