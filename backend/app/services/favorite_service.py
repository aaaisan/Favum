from typing import Dict, Optional, Any, Tuple
# from typing import Dict, List, Optional, Any, Tuple
import logging

from ..db.repositories.favorite_repository import FavoriteRepository
from ..db.repositories.post_repository import PostRepository
from ..core.exceptions import BusinessException
from ..schemas.responses.favorite import FavoriteListResponse, FavoriteDetailResponse, FavoriteDeleteResponse
from ..schemas.inputs.favorite import FavoriteCreate, FavoriteDelete

logger = logging.getLogger(__name__)

class FavoriteService:
    """收藏服务类
    
    提供用户帖子收藏相关的业务逻辑，包括添加收藏、取消收藏、查询收藏状态和获取收藏列表。
    """
    
    def __init__(self):
        """初始化收藏服务"""
        self.favorite_repository = FavoriteRepository()
        self.post_repository = PostRepository()
    
    async def get_user_favorites(self, user_id: int, skip: int = 0, limit: int = 100, only_public: bool = False) -> FavoriteListResponse:
        """获取用户收藏的帖子列表
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            only_public: 是否只返回公开内容
            
        Returns:
            Dict[str, Any]: 包含帖子列表和总数的字典
            
        Raises:
            BusinessException: 当操作失败时抛出业务异常
        """
        try:
            posts, total = await self.favorite_repository.get_user_favorites(user_id, skip, limit, only_public)
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
    
    async def add_favorite(self, post_id: int, user_id: int) -> FavoriteDetailResponse:
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
    
    async def remove_favorite(self, post_id: int, user_id: int) -> FavoriteDeleteResponse:
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
    
    async def check_post_exists(self, post_id: int) -> bool:
        """检查帖子是否存在
        
        Args:
            post_id: 帖子ID
            
        Returns:
            bool: 如果帖子存在且未被删除则返回True，否则返回False
        """
        try:
            post = await self.post_repository.get_with_relations(post_id)
            return post is not None
        except Exception as e:
            logger.error(f"检查帖子存在性失败: {str(e)}")
            return False
    
    async def get_favorite(self, post_id: int, user_id: int) -> Optional[FavoriteDetailResponse]:
        """获取收藏记录
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 收藏记录，不存在则返回None
        """
        try:
            return await self.favorite_repository.get_favorite(post_id, user_id)
        except Exception as e:
            logger.error(f"获取收藏记录失败: {str(e)}")
            return None
    
    async def favorite_post(self, favorite_data: FavoriteCreate) -> FavoriteDetailResponse:
        """收藏帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 包含收藏操作结果的字典
            
        Raises:
            BusinessException: 当帖子不存在或操作失败时抛出业务异常
        """
        try:
            # 添加收藏
            result = await self.favorite_repository.add_favorite(favorite_data.post_id, favorite_data.user_id)
            
            if not result.get("success"):
                raise BusinessException(
                    status_code=400,
                    error_code="FAVORITE_FAILED",
                    message=result.get("message", "收藏失败")
                )
            
            # 获取收藏记录
            favorite = await self.get_favorite(favorite_data.post_id, favorite_data.user_id)
            if not favorite:
                raise BusinessException(
                    status_code=500,
                    error_code="FAVORITE_NOT_FOUND",
                    message="收藏记录不存在"
                )
            
            return favorite
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            # 记录错误
            logger.error(f"收藏帖子失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="FAVORITE_FAILED",
                message="收藏帖子失败"
            ) 