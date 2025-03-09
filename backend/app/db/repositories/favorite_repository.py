from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc, join
from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc, join
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Tuple, Union
from typing import List, Optional, Dict, Any, Tuple, Union

from ..models.post_favorite import PostFavorite
from ..models.post import Post
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException

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
        async with self.session() as session:
            # 查询用户收藏的帖子总数
            count_query = select(func.count(PostFavorite.id)).where(
                PostFavorite.user_id == user_id
            )
            count_result = await session.execute(count_query)
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
            
            result = await session.execute(query)
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
        async with self.session() as session:
            query = select(PostFavorite).where(
                PostFavorite.post_id == post_id,
                PostFavorite.user_id == user_id
            )
            result = await session.execute(query)
            favorite = result.scalar_one_or_none()
            
            return favorite is not None
    
    async def add_favorite(self, post_id: int, user_id: int) -> Dict[str, Any]:
        """添加帖子到用户收藏
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            BusinessException: 当帖子不存在、已被删除或操作失败时抛出业务异常
        """
        async with self.session() as session:
            # 检查帖子是否存在且未被删除
            post_query = select(Post).where(
                Post.id == post_id,
                Post.is_deleted == False
            )
            post_result = await session.execute(post_query)
            post = post_result.scalar_one_or_none()
            
            if not post:
                raise BusinessException(
                    status_code=404,
                    error_code="POST_NOT_FOUND",
                    message="帖子不存在或已被删除"
                )
            
            # 检查用户是否已经收藏了该帖子
            already_favorited = await self.is_post_favorited(post_id, user_id)
            if already_favorited:
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
                session.add(favorite)
                await session.commit()
                
                return {
                    "success": True,
                    "message": "收藏成功"
                }
            except IntegrityError:
                await session.rollback()
                raise BusinessException(
                    status_code=400,
                    error_code="FAVORITE_FAILED",
                    message="收藏失败，请稍后重试"
                )
    
    async def remove_favorite(self, post_id: int, user_id: int) -> Dict[str, Any]:
        """从用户收藏中移除帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        async with self.session() as session:
            # 查找收藏记录
            query = select(PostFavorite).where(
                PostFavorite.post_id == post_id,
                PostFavorite.user_id == user_id
            )
            result = await session.execute(query)
            favorite = result.scalar_one_or_none()
            
            if not favorite:
                return {
                    "success": False,
                    "message": "您尚未收藏该帖子"
                }
            
            # 删除收藏记录
            await session.delete(favorite)
            await session.commit()
            
            return {
                "success": True,
                "message": "已取消收藏"
            } 