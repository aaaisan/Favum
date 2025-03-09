from typing import Dict, List, Optional, Any, Tuple
import logging

from ..db.repositories.tag_repository import TagRepository
from ..core.exceptions import BusinessException

logger = logging.getLogger(__name__)

class TagService:
    """标签服务类
    
    提供标签相关的业务逻辑，包括标签的创建、查询、更新和删除等功能。
    """
    
    def __init__(self):
        """初始化标签服务"""
        self.tag_repository = TagRepository()
    
    async def get_tag_detail(self, tag_id: int, include_deleted: bool = False) -> Dict[str, Any]:
        """获取标签详情
        
        Args:
            tag_id: 标签ID
            include_deleted: 是否包含已删除的标签
            
        Returns:
            Dict[str, Any]: 标签信息
            
        Raises:
            BusinessException: 当标签不存在时抛出业务异常
        """
        tag = await self.tag_repository.get_by_id(tag_id, include_deleted)
        
        if not tag:
            raise BusinessException(
                status_code=404,
                error_code="TAG_NOT_FOUND",
                message="标签不存在"
            )
            
        return tag
    
    async def get_tag_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取标签
        
        Args:
            name: 标签名称
            
        Returns:
            Optional[Dict[str, Any]]: 标签信息，不存在则返回None
        """
        return await self.tag_repository.get_by_name(name)
    
    async def get_tags(self, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取标签列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 标签列表和总数
        """
        return await self.tag_repository.get_all(skip, limit)
    
    async def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门标签
        
        Args:
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 热门标签列表
        """
        return await self.tag_repository.get_popular_tags(limit)
    
    async def get_recent_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用的标签
        
        Args:
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 最近使用的标签列表
        """
        return await self.tag_repository.get_recent_tags(limit)
    
    async def create_tag(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建标签
        
        Args:
            tag_data: 标签数据
            
        Returns:
            Dict[str, Any]: 创建的标签
            
        Raises:
            BusinessException: 当参数无效或创建失败时抛出业务异常
        """
        # 验证必要字段
        if "name" not in tag_data or not tag_data["name"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_NAME",
                message="标签名称不能为空"
            )
        
        # 创建标签
        try:
            tag = await self.tag_repository.create(tag_data)
            return tag
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"创建标签失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="CREATE_FAILED",
                message="创建标签失败"
            )
    
    async def update_tag(self, tag_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新标签
        
        Args:
            tag_id: 标签ID
            data: 更新的数据
            
        Returns:
            Dict[str, Any]: 更新后的标签
            
        Raises:
            BusinessException: 当标签不存在或更新失败时抛出业务异常
        """
        # 验证数据
        if "name" in data and not data["name"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_NAME",
                message="标签名称不能为空"
            )
        
        try:
            # 更新标签
            updated_tag = await self.tag_repository.update(tag_id, data)
            if not updated_tag:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            return updated_tag
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"更新标签失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="UPDATE_FAILED",
                message="更新标签失败"
            )
    
    async def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        """删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Dict[str, Any]: 删除结果信息
            
        Raises:
            BusinessException: 当标签不存在或删除失败时抛出业务异常
        """
        try:
            # 软删除标签
            success = await self.tag_repository.soft_delete(tag_id)
            if not success:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            return {"message": "标签已删除", "id": tag_id}
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"删除标签失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="DELETE_FAILED",
                message="删除标签失败"
            )
    
    async def restore_tag(self, tag_id: int) -> Dict[str, Any]:
        """恢复已删除的标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Dict[str, Any]: 恢复的标签
            
        Raises:
            BusinessException: 当标签不存在或未被删除时抛出业务异常
        """
        try:
            # 恢复标签
            restored_tag = await self.tag_repository.restore(tag_id)
            if not restored_tag:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            return restored_tag
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"恢复标签失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_FAILED",
                message="恢复标签失败"
            )
    
    async def update_tag_stats(self, tag_id: int) -> Dict[str, Any]:
        """更新标签统计信息
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Dict[str, Any]: 更新后的标签
            
        Raises:
            BusinessException: 当标签不存在或更新失败时抛出业务异常
        """
        try:
            # 更新统计信息
            updated_tag = await self.tag_repository.update_stats(tag_id)
            if not updated_tag:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            return updated_tag
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"更新标签统计信息失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="UPDATE_STATS_FAILED",
                message="更新标签统计信息失败"
            )
    
    async def get_posts_by_tag(self, tag_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取指定标签的帖子
        
        Args:
            tag_id: 标签ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
            
        Raises:
            BusinessException: 当标签不存在时抛出业务异常
        """
        try:
            # 获取标签帖子
            posts, total = await self.tag_repository.get_posts_by_tag(
                tag_id=tag_id,
                skip=skip,
                limit=limit
            )
            return posts, total
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"获取标签帖子失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="GET_POSTS_FAILED",
                message="获取标签帖子失败"
            )
    
    async def search_tags(self, query: str, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """搜索标签
        
        Args:
            query: 搜索关键词
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 标签列表和总数
        """
        try:
            # 搜索标签
            tags, total = await self.tag_repository.search_tags(
                query=query,
                skip=skip,
                limit=limit
            )
            return tags, total
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"搜索标签失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="SEARCH_FAILED",
                message="搜索标签失败"
            )
    
    async def get_related_tags(self, tag_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取关联标签
        
        查找与指定标签共同出现在帖子中的其他标签
        
        Args:
            tag_id: 标签ID
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 关联标签列表
            
        Raises:
            BusinessException: 当标签不存在时抛出业务异常
        """
        try:
            # 首先确认标签存在
            tag = await self.get_tag_detail(tag_id)
            if not tag:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            # 查询关联标签
            related_tags = await self.tag_repository.get_related_tags(tag_id, limit)
            return related_tags
        except BusinessException as e:
            # 直接抛出业务异常
            raise
        except Exception as e:
            logger.error(f"获取关联标签失败: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                error_code="GET_RELATED_TAGS_ERROR",
                message="获取关联标签失败"
            )
        
    async def get_tag_recommendations(self, keywords: Optional[List[str]] = None, user_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取标签推荐
        
        根据关键词和/或用户历史推荐标签
        
        Args:
            keywords: 关键词列表
            user_id: 用户ID，用于基于用户历史的推荐
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 推荐的标签列表
        """
        try:
            # 优先根据关键词推荐
            if keywords and len(keywords) > 0:
                # 清理关键词
                cleaned_keywords = [k.strip().lower() for k in keywords if k and k.strip()]
                if cleaned_keywords:
                    logger.info(f"根据关键词推荐标签: {cleaned_keywords}")
                    keyword_tags = await self.tag_repository.search_tags_by_keywords(cleaned_keywords, limit=limit)
                    if keyword_tags and len(keyword_tags) > 0:
                        return keyword_tags[0]  # 返回列表和计数中的列表部分
                    
            # 如果提供了用户ID，尝试根据用户历史推荐
            if user_id:
                logger.info(f"根据用户 {user_id} 历史推荐标签")
                user_tags = await self.tag_repository.get_tags_by_user_history(user_id, limit=limit)
                if user_tags and len(user_tags) > 0:
                    return user_tags
                    
            # 如果以上都没有结果，返回热门标签
            logger.info("回退到热门标签推荐")
            return await self.get_popular_tags(limit)
        except Exception as e:
            logger.error(f"获取标签推荐失败: {str(e)}", exc_info=True)
            # 出错时返回空列表而不是抛出异常，避免影响用户体验
            return []
        
    async def get_trending_tags(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """获取趋势标签
        
        获取指定天数内使用增长最快的标签
        
        Args:
            days: 天数范围
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 趋势标签列表
        """
        try:
            return await self.tag_repository.get_trending_tags(days, limit)
        except Exception as e:
            logger.error(f"获取趋势标签失败: {str(e)}", exc_info=True)
            # 出错时返回空列表
            return [] 