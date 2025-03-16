"""
帖子数据访问仓储

提供对Post实体的异步数据库操作封装，扩展基础Repository。
主要功能：
- 基本CRUD操作（继承自BaseRepository）
- 帖子特有的查询方法
- 分类和标签关联操作
- 投票和收藏统计
"""

from sqlalchemy import select, update, and_, func, desc, or_, join, text
from sqlalchemy.sql import expression
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from .base_repository import BaseRepository
from ..models import Post, User, Tag, Category, PostTag, PostVote, PostFavorite, Comment, Section
from ...core.database import async_get_db
from ...schemas.responses.post import (
    PostResponse,
    PostDetailResponse,
    PostListResponse,
    PostStatsResponse,
    PostVoteResponse,
    PostFavoriteResponse
)
from ...schemas.responses.tag import TagResponse

logger = logging.getLogger(__name__)

class PostRepository(BaseRepository[Post, PostResponse]):
    """Post实体的数据访问仓储类"""
    
    def __init__(self):
        """初始化帖子仓储
        
        设置模型类型为Post
        """
        super().__init__(Post, PostResponse)
    
    async def get_post_detail(self, post_id: int) -> Optional[PostDetailResponse]:
        """获取帖子详情
        
        Args:
            post_id: 帖子ID
            
        Returns:
            Optional[PostDetailResponse]: 帖子详情，不存在则返回None
        """
        async with async_get_db() as db:
            try:
                # 获取帖子
                result = await db.execute(
                    select(Post).where(
                        (Post.id == post_id) &
                        (Post.is_deleted == False)
                    )
                )
                post = result.scalar_one_or_none()
                
                if not post:
                    return None
                
                # 将帖子对象转换为字典
                post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                
                return PostDetailResponse(**post_dict)
            except Exception as e:
                logger.error(f"获取帖子详情失败: {str(e)}")
                return None
    
    async def get_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        section_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        query: Optional[str] = None,
        user_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[PostResponse], int]:
        """获取帖子列表
        
        Args:
            skip: 分页偏移量
            limit: 每页数量
            category_id: 分类ID过滤
            section_id: 版块ID过滤
            tag_id: 标签ID过滤
            query: 搜索关键词
            user_id: 作者ID过滤
            sort_by: 排序字段
            sort_order: 排序方向
            
        Returns:
            Tuple[List[PostResponse], int]: 帖子列表和总数
        """
        # 构建查询条件
        conditions = [Post.is_deleted == False]
        
        if category_id is not None:
            conditions.append(Post.category_id == category_id)
        
        if section_id is not None:
            conditions.append(Post.section_id == section_id)
        
        if user_id is not None:
            conditions.append(Post.author_id == user_id)
        
        if query:
            search_condition = or_(
                Post.title.ilike(f"%{query}%"),
                Post.content.ilike(f"%{query}%")
            )
            conditions.append(search_condition)
        
        # 处理标签过滤
        if tag_id is not None:
            # 使用子查询获取有特定标签的帖子ID
            tag_condition = Post.id.in_(
                select(PostTag.post_id).where(PostTag.tag_id == tag_id)
            )
            conditions.append(tag_condition)
        
        # 创建查询
        async with async_get_db() as db:
            try:
                # 构建主查询
                query = select(Post).where(and_(*conditions))
                
                # 排序
                if sort_by and hasattr(Post, sort_by):
                    sort_column = getattr(Post, sort_by)
                    if sort_order.lower() == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(sort_column)
                
                # 获取总数
                count_query = select(func.count()).select_from(
                    query.subquery()
                )
                count_result = await db.execute(count_query)
                total = count_result.scalar_one() or 0
                
                # 应用分页
                query = query.offset(skip).limit(limit)
                
                # 执行查询
                result = await db.execute(query)
                posts = result.scalars().all()
                
                # 将查询结果转换为响应模型
                post_responses = []
                for post in posts:
                    post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                    post_responses.append(PostResponse(**post_dict))
                
                return post_responses, total
            except Exception as e:
                logger.error(f"获取帖子列表失败: {str(e)}")
                return [], 0
    
    async def get_post_with_tags(self, post_id: int) -> Tuple[Optional[PostResponse], List[TagResponse]]:
        """获取帖子及其关联的标签
        
        Args:
            post_id: 帖子ID
            
        Returns:
            Tuple[Optional[PostResponse], List[TagResponse]]: 帖子和标签列表
        """
        async with async_get_db() as db:
            try:
                # 获取帖子
                post_result = await db.execute(
                    select(Post).where(
                        (Post.id == post_id) &
                        (Post.is_deleted == False)
                    )
                )
                post = post_result.scalar_one_or_none()
                
                if not post:
                    return None, []
                
                # 获取关联的标签
                tag_query = select(Tag).join(
                    PostTag, Tag.id == PostTag.tag_id
                ).where(
                    PostTag.post_id == post_id
                )
                
                tag_result = await db.execute(tag_query)
                tags = tag_result.scalars().all()
                
                # 转换为响应对象
                post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                post_response = PostResponse(**post_dict)
                
                tag_responses = []
                for tag in tags:
                    tag_dict = {c.name: getattr(tag, c.name) for c in tag.__table__.columns}
                    tag_responses.append(TagResponse(**tag_dict))
                
                return post_response, tag_responses
            except Exception as e:
                logger.error(f"获取帖子及标签失败: {str(e)}")
                return None, []
    
    async def increment_view_count(self, post_id: int) -> bool:
        """增加帖子的浏览次数
        
        Args:
            post_id: 帖子ID
            
        Returns:
            bool: 是否成功更新
        """
        async with async_get_db() as db:
            try:
                # 获取帖子
                post_result = await db.execute(
                    select(Post).where(Post.id == post_id)
                )
                post = post_result.scalar_one_or_none()
                
                if not post:
                    return False
                
                # 增加浏览次数
                post.view_count = (post.view_count or 0) + 1
                post.updated_at = datetime.now()
                
                await db.commit()
                return True
            except Exception as e:
                await db.rollback()
                logger.error(f"增加帖子浏览次数失败: {str(e)}")
                return False
    
    async def create_post_with_tags(
        self,
        post_data: Dict[str, Any],
        tag_ids: List[int] = None
    ) -> Optional[PostResponse]:
        """创建帖子并关联标签
        
        Args:
            post_data: 帖子数据
            tag_ids: 标签ID列表
            
        Returns:
            Optional[PostResponse]: 创建的帖子，失败则返回None
        """
        async with async_get_db() as db:
            try:
                # 创建帖子
                post = Post(**post_data)
                db.add(post)
                await db.flush()
                
                # 关联标签
                if tag_ids and len(tag_ids) > 0:
                    for tag_id in tag_ids:
                        post_tag = PostTag(post_id=post.id, tag_id=tag_id)
                        db.add(post_tag)
                
                await db.commit()
                await db.refresh(post)
                
                # 转换为响应对象
                post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                return PostResponse(**post_dict)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"创建帖子失败: {str(e)}")
                return None
    
    async def update_post_with_tags(
        self,
        post_id: int,
        post_data: Dict[str, Any],
        tag_ids: List[int] = None
    ) -> Optional[PostResponse]:
        """更新帖子和关联的标签
        
        Args:
            post_id: 帖子ID
            post_data: 帖子更新数据
            tag_ids: 标签ID列表
            
        Returns:
            Optional[PostResponse]: 更新后的帖子，失败则返回None
        """
        async with async_get_db() as db:
            try:
                # 获取帖子
                post_result = await db.execute(
                    select(Post).where(
                        (Post.id == post_id) &
                        (Post.is_deleted == False)
                    )
                )
                post = post_result.scalar_one_or_none()
                
                if not post:
                    return None
                
                # 更新帖子字段
                for key, value in post_data.items():
                    if hasattr(post, key):
                        setattr(post, key, value)
                
                post.updated_at = datetime.now()
                
                # 更新标签关联（如果提供了标签）
                if tag_ids is not None:
                    # 删除现有关联
                    await db.execute(
                        text(f"DELETE FROM post_tags WHERE post_id = {post_id}")
                    )
                    
                    # 添加新关联
                    for tag_id in tag_ids:
                        post_tag = PostTag(post_id=post_id, tag_id=tag_id)
                        db.add(post_tag)
                
                await db.commit()
                await db.refresh(post)
                
                # 转换为响应对象
                post_dict = {c.name: getattr(post, c.name) for c in post.__table__.columns}
                return PostResponse(**post_dict)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"更新帖子失败: {str(e)}")
                return None 