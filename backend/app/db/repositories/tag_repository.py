from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from ..models.tag import Tag
from ..models.post import Post
from ..models.post_tag import post_tags
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException

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
        async with self.session() as session:
            query = select(Tag).where(Tag.id == tag_id)
            
            if not include_deleted:
                query = query.where(Tag.is_deleted == False)
                
            result = await session.execute(query)
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
        async with self.session() as session:
            query = select(Tag).where(
                Tag.name == name,
                Tag.is_deleted == False
            )
            
            result = await session.execute(query)
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
        async with self.session() as session:
            # 查询标签
            query = (
                select(Tag)
                .where(Tag.is_deleted == False)
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            tags = result.scalars().all()
            
            # 查询总数
            count_query = select(func.count(Tag.id)).where(
                Tag.is_deleted == False
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            tags_list = [self.model_to_dict(tag) for tag in tags]
                
            return tags_list, total
    
    async def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门标签
        
        根据使用次数获取最热门的标签
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            List[Dict[str, Any]]: 热门标签列表
        """
        async with self.session() as session:
            query = (
                select(Tag)
                .where(Tag.is_deleted == False)
                .order_by(desc(Tag.post_count))
                .limit(limit)
            )
            
            result = await session.execute(query)
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
        async with self.session() as session:
            query = (
                select(Tag)
                .where(
                    Tag.is_deleted == False,
                    Tag.last_used_at.isnot(None)
                )
                .order_by(desc(Tag.last_used_at))
                .limit(limit)
            )
            
            result = await session.execute(query)
            tags = result.scalars().all()
            
            return [self.model_to_dict(tag) for tag in tags]
    
    async def create(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建标签
        
        Args:
            tag_data: 标签数据
            
        Returns:
            Dict[str, Any]: 创建的标签
        """
        async with self.session() as session:
            # 检查标签名称是否已存在
            name_query = select(Tag).where(
                Tag.name == tag_data["name"],
                Tag.is_deleted == False
            )
            name_result = await session.execute(name_query)
            existing = name_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="TAG_EXISTS",
                    message="标签名称已存在"
                )
            
            # 创建标签
            tag = Tag(**tag_data)
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
            
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
        async with self.session() as session:
            # 检查标签是否存在
            tag = await session.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return None
            
            # 如果更新名称，检查是否重复
            if "name" in data and data["name"] != tag.name:
                name_query = select(Tag).where(
                    Tag.name == data["name"],
                    Tag.is_deleted == False
                )
                name_result = await session.execute(name_query)
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
            
            await session.commit()
            await session.refresh(tag)
            
            # 返回更新后的标签
            return self.model_to_dict(tag)
    
    async def soft_delete(self, tag_id: int) -> bool:
        """软删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.session() as session:
            # 查询标签
            tag = await session.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return False
            
            # 检查是否有关联的帖子
            posts_query = select(func.count()).select_from(post_tags).where(
                post_tags.c.tag_id == tag_id
            )
            posts_result = await session.execute(posts_query)
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
            
            await session.commit()
            return True
    
    async def restore(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的标签，如果标签不存在或未被删除则返回None
        """
        async with self.session() as session:
            # 查询标签
            tag = await session.get(Tag, tag_id)
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
            existing_result = await session.execute(existing_query)
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
            
            await session.commit()
            await session.refresh(tag)
            
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
        async with self.session() as session:
            # 检查标签是否存在
            tag = await session.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                return None
            
            # 查询使用该标签的帖子数量
            posts_query = select(func.count()).select_from(post_tags).where(
                post_tags.c.tag_id == tag_id
            )
            posts_result = await session.execute(posts_query)
            post_count = posts_result.scalar() or 0
            
            # 更新统计信息
            tag.post_count = post_count
            
            # 如果有帖子使用了该标签，更新最后使用时间
            if post_count > 0:
                tag.last_used_at = datetime.now()
            
            await session.commit()
            await session.refresh(tag)
            
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
        async with self.session() as session:
            # 检查标签是否存在
            tag = await session.get(Tag, tag_id)
            if not tag or tag.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="TAG_NOT_FOUND",
                    message="标签不存在"
                )
                
            # 查询带有此标签的帖子
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
            
            result = await session.execute(query)
            posts = result.scalars().all()
            
            # 查询总数
            count_query = (
                select(func.count(Post.id))
                .join(post_tags, Post.id == post_tags.c.post_id)
                .where(
                    post_tags.c.tag_id == tag_id,
                    Post.is_deleted == False
                )
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            posts_list = []
            for post in posts:
                post_dict = {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                    "author_id": post.author_id
                }
                posts_list.append(post_dict)
                
            return posts_list, total
    
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
        async with self.session() as session:
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
            
            result = await session.execute(query_obj)
            tags = result.scalars().all()
            
            # 查询总数
            count_query = select(func.count(Tag.id)).where(
                Tag.is_deleted == False,
                or_(
                    Tag.name.ilike(search_term),
                    Tag.description.ilike(search_term)
                )
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            tags_list = [self.model_to_dict(tag) for tag in tags]
                
            return tags_list, total 