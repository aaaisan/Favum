from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc, join
# from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc, join
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Tuple, Union
from typing import List, Optional, Dict, Any, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from ..models.post_favorite import PostFavorite
from ..models.post import Post
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException
from ...core.database import async_get_db
from ...schemas.responses.post import PostResponse, PostFavoriteResponse
from ...schemas.responses.favorite import FavoriteListResponse

logger = logging.getLogger(__name__)

class FavoriteRepository(BaseRepository):
    """收藏仓库
    
    提供用户帖子收藏相关的数据库访问方法，包括添加收藏、取消收藏、查询收藏状态和获取收藏列表。
    """
    
    def __init__(self):
        """初始化收藏仓库"""
        super().__init__(PostFavorite)
    
    async def get_user_favorites(self, user_id: int, skip: int = 0, limit: int = 100, only_public: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户收藏的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            only_public: 是否只返回公开内容
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 收藏的帖子列表和总数
        """
        async with self.async_get_db() as db:
            # 查询用户收藏的帖子总数
            count_query = select(func.count(PostFavorite.id)).where(
                PostFavorite.user_id == user_id
            )
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 查询用户收藏的帖子
            query = (
                select(Post)
                .join(PostFavorite, PostFavorite.post_id == Post.id)
                .where(
                    PostFavorite.user_id == user_id,
                    Post.is_hidden == False,
                    Post.is_deleted == False
                )
                .order_by(desc(PostFavorite.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await db.execute(query)
            posts = result.scalars().all()
            
            # 转换帖子为字典形式
            posts_list = [self.model_to_dict(post) for post in posts]
            
            return posts_list, total
    
    async def is_post_favorited(self, post_id: int, user_id: int) -> bool:
        """检查用户是否已收藏指定帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            bool: 如果用户已收藏该帖子则返回True，否则返回False
        """
        async with self.async_get_db() as db:
            query = select(PostFavorite).where(
                PostFavorite.post_id == post_id,
                PostFavorite.user_id == user_id
            )
            result = await db.execute(query)
            favorite = result.scalar_one_or_none()
            
            return favorite is not None
    
    async def add_favorite(self, user_id: int, post_id: int) -> Optional[PostFavoriteResponse]:
        """添加收藏
        
        Args:
            user_id: 用户ID
            post_id: 帖子ID
            
        Returns:
            Optional[PostFavoriteResponse]: 收藏响应，失败则返回None
        """
        async with async_get_db() as db:
            try:
                # 检查是否已经收藏
                existing_query = select(PostFavorite).where(
                    and_(
                        PostFavorite.user_id == user_id,
                        PostFavorite.post_id == post_id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                
                if existing:
                    # 已经收藏过，返回现有记录
                    favorite_dict = {c.name: getattr(existing, c.name) for c in existing.__table__.columns}
                    return PostFavoriteResponse(
                        id=favorite_dict["id"],
                        user_id=favorite_dict["user_id"],
                        post_id=favorite_dict["post_id"],
                        created_at=favorite_dict["created_at"],
                        is_favorited=True,
                        message="帖子已经收藏过了"
                    )
                
                # 检查帖子是否存在
                post_query = select(Post).where(
                    and_(
                        Post.id == post_id,
                        Post.is_deleted == False
                    )
                )
                post_result = await db.execute(post_query)
                post = post_result.scalar_one_or_none()
                
                if not post:
                    return None
                
                # 添加收藏
                favorite = PostFavorite(
                    user_id=user_id,
                    post_id=post_id,
                    created_at=datetime.now()
                )
                db.add(favorite)
                
                # 更新帖子收藏计数
                post.favorites_count = (post.favorites_count or 0) + 1
                
                await db.commit()
                await db.refresh(favorite)
                
                # 构建响应
                return PostFavoriteResponse(
                    id=favorite.id,
                    user_id=favorite.user_id,
                    post_id=favorite.post_id,
                    created_at=favorite.created_at,
                    is_favorited=True,
                    message="帖子收藏成功"
                )
            except Exception as e:
                await db.rollback()
                logger.error(f"添加收藏失败: {str(e)}")
                return None
    
    async def remove_favorite(self, user_id: int, post_id: int) -> Optional[PostFavoriteResponse]:
        """取消收藏
        
        Args:
            user_id: 用户ID
            post_id: 帖子ID
            
        Returns:
            Optional[PostFavoriteResponse]: 收藏响应，失败则返回None
        """
        async with async_get_db() as db:
            try:
                # 检查收藏是否存在
                existing_query = select(PostFavorite).where(
                    and_(
                        PostFavorite.user_id == user_id,
                        PostFavorite.post_id == post_id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    # 没有收藏过，返回空响应
                    return PostFavoriteResponse(
                        id=0,
                        user_id=user_id,
                        post_id=post_id,
                        created_at=datetime.now(),
                        is_favorited=False,
                        message="帖子未收藏"
                    )
                
                # 删除收藏
                delete_query = delete(PostFavorite).where(
                    and_(
                        PostFavorite.user_id == user_id,
                        PostFavorite.post_id == post_id
                    )
                )
                await db.execute(delete_query)
                
                # 更新帖子收藏计数
                post_query = select(Post).where(Post.id == post_id)
                post_result = await db.execute(post_query)
                post = post_result.scalar_one_or_none()
                
                if post and post.favorites_count and post.favorites_count > 0:
                    post.favorites_count -= 1
                
                await db.commit()
                
                # 构建响应
                return PostFavoriteResponse(
                    id=0,
                    user_id=user_id,
                    post_id=post_id,
                    created_at=datetime.now(),
                    is_favorited=False,
                    message="取消收藏成功"
                )
            except Exception as e:
                await db.rollback()
                logger.error(f"取消收藏失败: {str(e)}")
                return None
    
    async def check_favorite(self, user_id: int, post_id: int) -> bool:
        """检查用户是否已收藏帖子
        
        Args:
            user_id: 用户ID
            post_id: 帖子ID
            
        Returns:
            bool: 是否已收藏
        """
        async with async_get_db() as db:
            try:
                query = select(PostFavorite).where(
                    and_(
                        PostFavorite.user_id == user_id,
                        PostFavorite.post_id == post_id
                    )
                )
                result = await db.execute(query)
                favorite = result.scalar_one_or_none()
                
                return favorite is not None
            except Exception as e:
                logger.error(f"检查收藏状态失败: {str(e)}")
                return False
    
    async def get_user_favorites(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[PostResponse], int]:
        """获取用户收藏的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 分页偏移量
            limit: 每页数量
            
        Returns:
            Tuple[List[PostResponse], int]: 帖子列表和总数
        """
        async with async_get_db() as db:
            try:
                # 获取用户收藏的帖子ID
                favorite_query = select(PostFavorite.post_id).where(
                    PostFavorite.user_id == user_id
                ).order_by(desc(PostFavorite.created_at))
                
                favorite_result = await db.execute(favorite_query)
                favorite_post_ids = [row[0] for row in favorite_result.all()]
                
                # 获取总数
                total = len(favorite_post_ids)
                
                # 应用分页
                paginated_post_ids = favorite_post_ids[skip:skip+limit] if favorite_post_ids else []
                
                if not paginated_post_ids:
                    return [], 0
                
                # 获取帖子详情
                posts_query = select(Post).where(
                    and_(
                        Post.id.in_(paginated_post_ids),
                        Post.is_deleted == False
                    )
                )
                
                posts_result = await db.execute(posts_query)
                posts = posts_result.scalars().all()
                
                # 转换为响应对象
                post_responses = []
                for post in posts:
                    post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                    post_responses.append(PostResponse(**post_dict))
                
                # 确保按照收藏顺序排序
                sorted_responses = []
                for post_id in paginated_post_ids:
                    for post in post_responses:
                        if post.id == post_id:
                            sorted_responses.append(post)
                            break
                
                return sorted_responses, total
            except Exception as e:
                logger.error(f"获取用户收藏列表失败: {str(e)}")
                return [], 0 