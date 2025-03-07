from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from ..db.repositories.favorite_repository import FavoriteRepository
from ..core.exceptions import BusinessException

logger = logging.getLogger(__name__)

class FavoriteService:
    """收藏服务类
    
    提供用户帖子收藏相关的业务逻辑，包括添加收藏、取消收藏、查询收藏状态和获取收藏列表。
    """
    
    def __init__(self):
        """初始化收藏服务"""
        self.favorite_repository = FavoriteRepository()
    
    async def get_user_favorites(self, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取用户收藏的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Dict[str, Any]: 包含帖子列表和总数的字典
            
        Raises:
            BusinessException: 当操作失败时抛出业务异常
        """
        try:
            posts, total = await self.favorite_repository.get_user_favorites(user_id, skip, limit)
            return {
                "posts": posts,
                "total": total
            }
        except Exception as e:
            logger.error(f"获取用户收藏列表失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="GET_FAVORITES_FAILED",
                message="获取收藏列表失败"
            )
    
    async def is_post_favorited(self, post_id: int, user_id: int) -> bool:
        """检查用户是否已收藏指定帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            bool: 如果用户已收藏该帖子则返回True，否则返回False
        """
        try:
            return await self.favorite_repository.is_post_favorited(post_id, user_id)
        except Exception as e:
            logger.error(f"检查收藏状态失败: {str(e)}")
            # 在查询状态时，如果发生错误，默认返回未收藏状态
            return False
    
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
        try:
            return await self.favorite_repository.add_favorite(post_id, user_id)
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"添加收藏失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="ADD_FAVORITE_FAILED",
                message="添加收藏失败"
            )
    
    async def remove_favorite(self, post_id: int, user_id: int) -> Dict[str, Any]:
        """从用户收藏中移除帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            BusinessException: 当操作失败时抛出业务异常
        """
        try:
            return await self.favorite_repository.remove_favorite(post_id, user_id)
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"取消收藏失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="REMOVE_FAVORITE_FAILED",
                message="取消收藏失败"
            ) 