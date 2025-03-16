from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from ..models.tag import Tag
from ..models.post import Post
from ..models.post_tag import post_tags
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException
import logging
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

class TagRepository(BaseRepository):
    """标签仓库
    
    提供标签相关的数据库访问方法，包括查询、创建、更新和删除标签。
    """
    
    def __init__(self):
        """初始化标签仓库"""
        super().__init__(Tag)
    
    async def get_by_id(self, tag_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """根据ID获取标签
        
        Args:
            tag_id: 标签ID
            include_deleted: 是否包含已删除的标签
            
        Returns:
            Optional[Dict[str, Any]]: 标签信息字典，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = select(Tag).where(Tag.id == tag_id)
            
            if not include_deleted:
                query = query.where(Tag.is_deleted == False)
                
            result = await db.execute(query)
            tag = result.scalar_one_or_none()
            
            if tag is None:
                return None
                
            return self.model_to_dict(tag)
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取标签
        
        Args:
            name: 标签名称
            
        Returns:
            Optional[Dict[str, Any]]: 标签信息字典，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = select(Tag).where(
                Tag.name == name,
                Tag.is_deleted == False
            )
            
            result = await db.execute(query)
            tag = result.scalar_one_or_none()
            
            if tag is None:
                return None
                
            return self.model_to_dict(tag)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有标签
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 标签列表和总数
        """
        async with self.async_get_db() as db:
            try:
                # 查询标签
                query = (
                    select(Tag)
                    .where(Tag.is_deleted == False)
                    .offset(skip)
                    .limit(limit)
                )
                
                result = await db.execute(query)
                tags = result.scalars().all()
                
                # 查询总数
                count_query = select(func.count(Tag.id)).where(Tag.is_deleted == False)
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
                
                # 处理结果
                tags_data = []
                for tag in tags:
                    tag_dict = tag.to_dict() if hasattr(tag, 'to_dict') else {
                        "id": tag.id,
                        "name": tag.name,
                        "created_at": tag.created_at,
                        "updated_at": tag.updated_at if hasattr(tag, 'updated_at') else None,
                        "is_deleted": tag.is_deleted,
                        "post_count": tag.post_count if hasattr(tag, 'post_count') else 0
                    }
                    tags_data.append(tag_dict)
                
                return tags_data, total
            except Exception as e:
                logger.error(f"获取所有标签失败: {str(e)}", exc_info=True)
                return [], 0
    
    async def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门标签
        
        根据使用次数获取最热门的标签
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            List[Dict[str, Any]]: 热门标签列表
        """
        async with self.async_get_db() as db:
            query = (
                select(Tag)
                .where(Tag.is_deleted == False)
                .order_by(desc(Tag.post_count))
                .limit(limit)
            )
            
            result = await db.execute(query)
            tags = result.scalars().all()
            
            return [self.model_to_dict(tag) for tag in tags]
    
    async def get_recent_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近使用的标签
        
        根据最后使用时间获取最近使用的标签
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            List[Dict[str, Any]]: 最近使用的标签列表
        """
        async with self.async_get_db() as db:
            query = (
                select(Tag)
                .where(
                    Tag.is_deleted == False,
                    Tag.last_used_at.isnot(None)
                )
                .order_by(desc(Tag.last_used_at))
                .limit(limit)
            )
            
            result = await db.execute(query)
            tags = result.scalars().all()
            
            return [self.model_to_dict(tag) for tag in tags]
    
    async def create(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建标签
        
        Args:
            tag_data: 标签数据
            
        Returns:
            Dict[str, Any]: 创建的标签
        """
        async with self.async_get_db() as db:
            # 检查标签名称是否已存在
            name_query = select(Tag).where(
                Tag.name == tag_data["name"],
                Tag.is_deleted == False
            )
            name_result = await db.execute(name_query)
            existing = name_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="TAG_EXISTS",
                    message="标签名称已存在"
                )
            
            # 创建标签
            tag = Tag(**tag_data)
            db.add(tag)
            await db.commit()
            await db.refresh(tag)
            
            # 返回创建的标签
            return self.model_to_dict(tag)
    
    async def update(self, tag_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新标签
        
        Args:
            tag_id: 标签ID
            data: 要更新的数据
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的标签，不存在则返回None
        """
        async with self.async_get_db() as db:
            # 检查标签是否存在
            tag = await db.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return None
            
            # 如果更新名称，检查是否重复
            if "name" in data and data["name"] != tag.name:
                name_query = select(Tag).where(
                    Tag.name == data["name"],
                    Tag.is_deleted == False
                )
                name_result = await db.execute(name_query)
                existing = name_result.scalar_one_or_none()
                
                if existing is not None:
                    raise BusinessException(
                        status_code=400,
                        error_code="TAG_EXISTS",
                        message="标签名称已存在"
                    )
            
            # 更新标签
            for key, value in data.items():
                if hasattr(tag, key) and key != "id":
                    setattr(tag, key, value)
            
            await db.commit()
            await db.refresh(tag)
            
            # 返回更新后的标签
            return self.model_to_dict(tag)
    
    async def soft_delete(self, tag_id: int) -> bool:
        """软删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 查询标签
            tag = await db.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return False
            
            # 检查是否有关联的帖子
            posts_query = select(func.count()).select_from(post_tags).where(
                post_tags.c.tag_id == tag_id
            )
            posts_result = await db.execute(posts_query)
            posts_count = posts_result.scalar() or 0
            
            if posts_count > 0:
                raise BusinessException(
                    status_code=400,
                    error_code="HAS_POSTS",
                    message="不能删除已被使用的标签"
                )
            
            # 软删除标签
            tag.is_deleted = True
            tag.deleted_at = datetime.now()
            
            await db.commit()
            return True
    
    async def restore(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的标签，如果标签不存在或未被删除则返回None
        """
        async with self.async_get_db() as db:
            # 查询标签
            tag = await db.get(Tag, tag_id)
            if not tag:
                return None
            
            # 如果标签未被删除，则无需恢复
            if not tag.is_deleted:
                raise BusinessException(
                    status_code=400,
                    error_code="TAG_NOT_DELETED",
                    message="标签未被删除"
                )
            
            # 检查是否有同名未删除标签
            existing_query = select(Tag).where(
                Tag.name == tag.name,
                Tag.id != tag_id,
                Tag.is_deleted == False
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="DUPLICATE_TAG",
                    message="已存在同名标签，无法恢复"
                )
            
            # 恢复标签
            tag.is_deleted = False
            tag.deleted_at = None
            
            await db.commit()
            await db.refresh(tag)
            
            # 返回恢复后的标签
            return self.model_to_dict(tag)
    
    async def update_stats(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """更新标签统计信息
        
        更新标签的使用次数和最后使用时间
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的标签，不存在则返回None
        """
        async with self.async_get_db() as db:
            # 检查标签是否存在
            tag = await db.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return None
            
            # 查询使用该标签的帖子数量
            posts_query = select(func.count()).select_from(post_tags).where(
                post_tags.c.tag_id == tag_id
            )
            posts_result = await db.execute(posts_query)
            post_count = posts_result.scalar() or 0
            
            # 更新统计信息
            tag.post_count = post_count
            
            # 如果有帖子使用了该标签，更新最后使用时间
            if post_count > 0:
                tag.last_used_at = datetime.now()
            
            await db.commit()
            await db.refresh(tag)
            
            # 返回更新后的标签
            return self.model_to_dict(tag)
    
    async def get_posts_by_tag(self, tag_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取带有指定标签的帖子
        
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
            logger.info(f"开始查询标签 {tag_id} 的帖子，跳过: {skip}, 限制: {limit}")
            
            # 首先检查标签是否存在
            tag = await self.get_by_id(tag_id)
            if not tag:
                raise BusinessException(
                    code="TAG_NOT_FOUND",
                    message="标签不存在",
                    status_code=404
                )
                
            async with self.async_get_db() as db:
                # 构建查询 - 使用left join确保能获取到帖子的所有相关标签
                query = (
                    select(Post)
                    .join(post_tags, Post.id == post_tags.c.post_id)
                    .where(
                        post_tags.c.tag_id == tag_id,
                        Post.is_deleted == False
                    )
                    .order_by(desc(Post.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                
                result = await db.execute(query)
                posts = result.unique().scalars().all()
                
                logger.info(f"查询到 {len(posts)} 篇帖子")
                
                # 查询总数
                count_query = (
                    select(func.count(Post.id.distinct()))
                    .select_from(Post)
                    .join(post_tags, Post.id == post_tags.c.post_id)
                    .where(
                        post_tags.c.tag_id == tag_id,
                        Post.is_deleted == False
                    )
                )
                count_result = await db.execute(count_query)
                total = count_result.scalar() or 0
                
                # 处理结果
                posts_list = []
                for post in posts:
                    try:
                        # 获取帖子的基本信息
                        post_dict = {
                            "id": post.id,
                            "title": post.title,
                            "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                            "author_id": post.author_id,
                            "section_id": post.section_id,
                            "category_id": post.category_id,
                            "is_hidden": post.is_hidden,
                            "created_at": post.created_at.isoformat() if hasattr(post.created_at, 'isoformat') else post.created_at,
                            "updated_at": post.updated_at.isoformat() if hasattr(post.updated_at, 'isoformat') else post.updated_at,
                            "is_deleted": post.is_deleted,
                            "vote_count": post.vote_count if hasattr(post, 'vote_count') else 0,
                        }
                        
                        # 添加分类信息
                        if post.category:
                            category_dict = {
                                "id": post.category.id,
                                "name": post.category.name,
                                "description": post.category.description,
                                "created_at": post.category.created_at.isoformat() if hasattr(post.category.created_at, 'isoformat') else post.category.created_at
                            }
                            post_dict["category"] = category_dict
                        else:
                            post_dict["category"] = None
                            
                        # 添加版块信息
                        if post.section:
                            section_dict = {
                                "id": post.section.id,
                                "name": post.section.name,
                                "description": post.section.description,
                                "created_at": post.section.created_at.isoformat() if hasattr(post.section.created_at, 'isoformat') else post.section.created_at
                            }
                            post_dict["section"] = section_dict
                        else:
                            post_dict["section"] = None
                            
                        # 添加标签信息
                        if post.tags:
                            post_dict["tags"] = [{
                                "id": tag.id,
                                "name": tag.name,
                                "created_at": tag.created_at.isoformat() if hasattr(tag.created_at, 'isoformat') else tag.created_at,
                                "post_count": tag.post_count if hasattr(tag, 'post_count') else 0
                            } for tag in post.tags]
                        else:
                            post_dict["tags"] = []
                            
                        post_dict["comments"] = None
                        posts_list.append(post_dict)
                    except Exception as e:
                        logger.error(f"处理帖子 {post.id} 失败: {str(e)}", exc_info=True)
                        continue
                
                return posts_list, total
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取标签 {tag_id} 的帖子失败: {str(e)}", exc_info=True)
            raise BusinessException(
                code="GET_POSTS_FAILED",
                message="获取帖子失败",
                status_code=500
            )
    
    async def search_tags(self, query: str, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """搜索标签
        
        根据关键词搜索标签
        
        Args:
            query: 搜索关键词
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 标签列表和总数
        """
        async with self.async_get_db() as db:
            # 构建搜索条件
            search_term = f"%{query}%"
            
            # 查询标签
            query_obj = (
                select(Tag)
                .where(
                    Tag.is_deleted == False,
                    or_(
                        Tag.name.ilike(search_term),
                        Tag.description.ilike(search_term)
                    )
                )
                .order_by(desc(Tag.post_count))
                .offset(skip)
                .limit(limit)
            )
            
            result = await db.execute(query_obj)
            tags = result.scalars().all()
            
            # 查询总数
            count_query = select(func.count(Tag.id)).where(
                Tag.is_deleted == False,
                or_(
                    Tag.name.ilike(search_term),
                    Tag.description.ilike(search_term)
                )
            )
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            tags_list = [self.model_to_dict(tag) for tag in tags]
                
            return tags_list, total
    
    async def get_related_tags(self, tag_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取关联标签
        
        查找与指定标签共同出现在帖子中的其他标签
        
        Args:
            tag_id: 标签ID
            limit: 返回的标签数量
            
        Returns:
            List[Dict[str, Any]]: 关联标签列表
        """
        try:
            async with self.async_get_db() as db:
                # 使用SQL子查询找出包含该标签的所有帖子
                posts_with_tag_subquery = (
                    select(post_tags.c.post_id)
                    .where(post_tags.c.tag_id == tag_id)
                    .distinct()
                    .subquery()
                )
                
                # 找出这些帖子中出现的其他标签
                query = (
                    select(Tag, func.count(post_tags.c.post_id).label("common_posts"))
                    .join(post_tags, Tag.id == post_tags.c.tag_id)
                    .where(
                        post_tags.c.post_id.in_(select(posts_with_tag_subquery.c.post_id)),
                        Tag.id != tag_id,  # 排除自身
                        Tag.is_deleted == False
                    )
                    .group_by(Tag.id)
                    .order_by(desc("common_posts"))
                    .limit(limit)
                )
                
                result = await db.execute(query)
                related_tags = result.all()
                
                # 处理结果
                return [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "post_count": tag.post_count,
                        "common_posts": common_count,
                        "created_at": tag.created_at.isoformat() if hasattr(tag.created_at, 'isoformat') else tag.created_at
                    }
                    for tag, common_count in related_tags
                ]
        except Exception as e:
            logger.error(f"获取关联标签失败: {str(e)}", exc_info=True)
            return []
        
    async def search_tags_by_keywords(self, keywords: List[str], limit: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """根据关键词列表搜索标签
        
        Args:
            keywords: 关键词列表
            limit: 返回的最大标签数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 标签列表和总数
        """
        try:
            async with self.async_get_db() as db:
                # 构建OR条件，匹配任一关键词
                conditions = []
                for keyword in keywords:
                    conditions.append(Tag.name.ilike(f"%{keyword}%"))
                
                # 查询标签
                query = (
                    select(Tag)
                    .where(
                        or_(*conditions),
                        Tag.is_deleted == False
                    )
                    .order_by(desc(Tag.post_count))
                    .limit(limit)
                )
                
                result = await db.execute(query)
                tags = result.scalars().all()
                
                # 查询总数
                count_query = (
                    select(func.count(Tag.id))
                    .where(
                        or_(*conditions),
                        Tag.is_deleted == False
                    )
                )
                count_result = await db.execute(count_query)
                total = count_result.scalar() or 0
                
                # 处理结果
                return [self.model_to_dict(tag) for tag in tags], total
        except Exception as e:
            logger.error(f"关键词搜索标签失败: {str(e)}", exc_info=True)
            return [], 0
        
    async def get_tags_by_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户历史中使用的标签
        
        Args:
            user_id: 用户ID
            limit: 返回的最大标签数量
            
        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        try:
            async with self.async_get_db() as db:
                # 找出用户发布的所有帖子
                user_posts_subquery = (
                    select(Post.id)
                    .where(
                        Post.author_id == user_id,
                        Post.is_deleted == False
                    )
                    .subquery()
                )
                
                # 找出这些帖子中使用的标签
                query = (
                    select(Tag, func.count(post_tags.c.post_id).label("usage_count"))
                    .join(post_tags, Tag.id == post_tags.c.tag_id)
                    .where(
                        post_tags.c.post_id.in_(select(user_posts_subquery.c.id)),
                        Tag.is_deleted == False
                    )
                    .group_by(Tag.id)
                    .order_by(desc("usage_count"), desc(Tag.last_used_at))
                    .limit(limit)
                )
                
                result = await db.execute(query)
                user_tags = result.all()
                
                # 处理结果
                return [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "post_count": tag.post_count,
                        "user_usage_count": usage_count,
                        "created_at": tag.created_at.isoformat() if hasattr(tag.created_at, 'isoformat') else tag.created_at
                    }
                    for tag, usage_count in user_tags
                ]
        except Exception as e:
            logger.error(f"获取用户历史标签失败: {str(e)}", exc_info=True)
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
            async with self.async_get_db() as db:
                # 计算日期范围
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # 找出这段时间内创建的帖子
                recent_posts_subquery = (
                    select(Post.id)
                    .where(
                        Post.created_at >= start_date,
                        Post.created_at <= end_date,
                        Post.is_deleted == False
                    )
                    .subquery()
                )
                
                # 查询这些帖子中使用的标签
                query = (
                    select(Tag, func.count(post_tags.c.post_id).label("recent_count"))
                    .join(post_tags, Tag.id == post_tags.c.tag_id)
                    .where(
                        post_tags.c.post_id.in_(select(recent_posts_subquery.c.id)),
                        Tag.is_deleted == False
                    )
                    .group_by(Tag.id)
                    .order_by(desc("recent_count"))
                    .limit(limit)
                )
                
                result = await db.execute(query)
                trending_tags = result.all()
                
                # 处理结果
                return [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "post_count": tag.post_count,
                        "recent_posts": recent_count,
                        "created_at": tag.created_at.isoformat() if hasattr(tag.created_at, 'isoformat') else tag.created_at
                    }
                    for tag, recent_count in trending_tags
                ]
        except Exception as e:
            logger.error(f"获取趋势标签失败: {str(e)}", exc_info=True)
            return [] 