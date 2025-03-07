"""
帖子数据访问仓储

提供对Post实体的异步数据库操作封装，扩展基础Repository。
主要功能：
- 基本CRUD操作（继承自BaseRepository）
- 帖子特定查询方法
- 标签关联操作
- 投票相关操作
- 支持软删除和恢复
"""

from sqlalchemy import select, and_, or_, func, update, insert, delete, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .base_repository import BaseRepository
from ..models import Post, Tag, post_tags, PostVote, VoteType, Category, Section, User
from ...core.exceptions import BusinessError

class PostRepository(BaseRepository):
    """Post实体的数据访问仓储类"""
    
    def __init__(self):
        """初始化帖子仓储
        
        设置模型类型为Post
        """
        super().__init__(Post)
    
    async def get_with_relations(self, post_id: int, include_hidden: bool = False) -> Optional[Dict[str, Any]]:
        """获取帖子及其关联信息
        
        加载帖子的分类、版块、标签等关联信息
        
        Args:
            post_id: 帖子ID
            include_hidden: 是否包含隐藏的帖子
            
        Returns:
            Optional[Dict[str, Any]]: 帖子数据字典，不存在则返回None
        """
        # 构建查询条件
        conditions = [self.model.id == post_id, self.model.is_deleted == False]
        if not include_hidden:
            conditions.append(self.model.is_hidden == False)
            
        # 构建查询，加载关联实体
        query = (
            select(self.model)
            .options(
                joinedload(self.model.category),
                joinedload(self.model.section),
                joinedload(self.model.tags)
            )
            .where(and_(*conditions))
        )
        
        # 执行查询
        result = await self.db.execute(query)
        post = result.unique().scalar_one_or_none()
        
        return post.to_dict(include_relations=True) if post else None
    
    async def get_posts(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        include_hidden: bool = False,
        category_id: Optional[int] = None,
        section_id: Optional[int] = None,
        author_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取帖子列表
        
        支持多种过滤条件和排序
        
        Args:
            skip: 分页偏移
            limit: 每页数量
            include_hidden: 是否包含隐藏的帖子
            category_id: 按分类ID筛选
            section_id: 按版块ID筛选
            author_id: 按作者ID筛选
            tag_ids: 按标签ID列表筛选
            sort_field: 排序字段
            sort_order: 排序顺序("asc"或"desc")
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        # 构建基础查询条件
        conditions = [self.model.is_deleted == False]
        if not include_hidden:
            conditions.append(self.model.is_hidden == False)
            
        # 添加筛选条件
        if category_id:
            conditions.append(self.model.category_id == category_id)
        if section_id:
            conditions.append(self.model.section_id == section_id)
        if author_id:
            conditions.append(self.model.author_id == author_id)
            
        # 构建查询，加载关联实体
        query = (
            select(self.model)
            .options(
                joinedload(self.model.category),
                joinedload(self.model.section),
                joinedload(self.model.tags)
            )
            .where(and_(*conditions))
        )
        
        # 处理标签筛选
        if tag_ids:
            # 使用exists子查询检查帖子是否包含指定标签
            for tag_id in tag_ids:
                subquery = (
                    select(post_tags.c.post_id)
                    .where(
                        and_(
                            post_tags.c.post_id == self.model.id,
                            post_tags.c.tag_id == tag_id
                        )
                    )
                    .exists()
                )
                query = query.where(subquery)
                
        # 处理排序
        if sort_field:
            sort_attr = getattr(self.model, sort_field, self.model.created_at)
            query = query.order_by(desc(sort_attr) if sort_order == "desc" else asc(sort_attr))
        else:
            # 默认按创建时间降序排列
            query = query.order_by(desc(self.model.created_at))
            
        # 添加分页
        query = query.offset(skip).limit(limit)
        
        # 执行查询
        result = await self.db.execute(query)
        posts = result.unique().scalars().all()
        posts_data = [post.to_dict(include_relations=True) for post in posts]
        
        # 获取总数
        count_query = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        return posts_data, total
    
    async def update_tags(self, post_id: int, tag_ids: List[int]) -> bool:
        """更新帖子的标签关联
        
        完全替换帖子的标签列表
        
        Args:
            post_id: 帖子ID
            tag_ids: 标签ID列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 首先删除所有现有的标签关联
            delete_stmt = delete(post_tags).where(post_tags.c.post_id == post_id)
            await self.db.execute(delete_stmt)
            
            # 然后插入新的标签关联
            for tag_id in tag_ids:
                insert_stmt = insert(post_tags).values(post_id=post_id, tag_id=tag_id)
                await self.db.execute(insert_stmt)
                
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def toggle_visibility(self, post_id: int, is_hidden: bool) -> bool:
        """切换帖子可见性
        
        Args:
            post_id: 帖子ID
            is_hidden: 是否隐藏
            
        Returns:
            bool: 操作是否成功
        """
        # 构建更新语句
        stmt = (
            update(self.model)
            .where(self.model.id == post_id)
            .values(
                is_hidden=is_hidden,
                updated_at=datetime.now()
            )
        )
        
        # 执行更新
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # 检查是否找到并更新了记录
        return result.rowcount > 0
    
    async def get_user_vote(self, post_id: int, user_id: int) -> Optional[str]:
        """获取用户对帖子的投票状态
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Optional[str]: 投票类型，'upvote'、'downvote'或None
        """
        query = select(PostVote).where(
            and_(
                PostVote.post_id == post_id,
                PostVote.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        vote = result.scalar_one_or_none()
        
        return vote.vote_type.value if vote else None
    
    async def vote_post(self, post_id: int, user_id: int, vote_type: str) -> Dict[str, Any]:
        """对帖子进行投票
        
        使用事务处理保证原子性，处理以下情况：
        - 首次投票：插入新投票记录
        - 改变投票：更新现有投票
        - 取消投票：删除投票记录
        - 同时更新帖子的vote_count
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            vote_type: 投票类型，'upvote'、'downvote'或'none'
            
        Returns:
            Dict[str, Any]: 包含操作结果和新投票计数的字典
            
        Raises:
            BusinessError: 当帖子不存在时
        """
        # 开始事务
        async with self.db.begin():
            # 检查帖子是否存在
            post_query = select(self.model).where(
                and_(
                    self.model.id == post_id,
                    self.model.is_deleted == False
                )
            )
            post_result = await self.db.execute(post_query)
            post = post_result.scalar_one_or_none()
            
            if not post:
                raise BusinessError(message="帖子不存在", code="post_not_found")
                
            # 查询当前投票状态
            vote_query = select(PostVote).where(
                and_(
                    PostVote.post_id == post_id,
                    PostVote.user_id == user_id
                )
            )
            vote_result = await self.db.execute(vote_query)
            current_vote = vote_result.scalar_one_or_none()
            
            old_vote_type = current_vote.vote_type.value if current_vote else "none"
            vote_count_change = 0
            
            # 根据新旧投票状态决定操作
            if vote_type == "none":
                # 取消投票
                if current_vote:
                    if current_vote.vote_type == VoteType.upvote:
                        vote_count_change = -1
                    elif current_vote.vote_type == VoteType.downvote:
                        vote_count_change = 1
                        
                    await self.db.delete(current_vote)
            elif not current_vote:
                # 新增投票
                new_vote = PostVote(
                    post_id=post_id,
                    user_id=user_id,
                    vote_type=VoteType.upvote if vote_type == "upvote" else VoteType.downvote,
                    created_at=datetime.now()
                )
                self.db.add(new_vote)
                
                if vote_type == "upvote":
                    vote_count_change = 1
                else:
                    vote_count_change = -1
            else:
                # 修改现有投票
                if current_vote.vote_type == VoteType.upvote:
                    if vote_type == "downvote":
                        vote_count_change = -2  # 从赞变踩，-2分
                        current_vote.vote_type = VoteType.downvote
                # 从踩变赞，+2分
                elif current_vote.vote_type == VoteType.downvote:
                    if vote_type == "upvote":
                        vote_count_change = 2
                        current_vote.vote_type = VoteType.upvote
                        
                current_vote.updated_at = datetime.now()
                
            # 更新帖子的投票计数
            if vote_count_change != 0:
                update_stmt = (
                    update(self.model)
                    .where(self.model.id == post_id)
                    .values(vote_count=self.model.vote_count + vote_count_change)
                )
                await self.db.execute(update_stmt)
                
            # 提交事务（事务在with块结束时自动提交）
                
        # 获取最新投票计数
        count_query = select(self.model.vote_count).where(self.model.id == post_id)
        count_result = await self.db.execute(count_query)
        new_vote_count = count_result.scalar_one()
        
        return {
            "old_vote": old_vote_type,
            "new_vote": vote_type,
            "vote_count": new_vote_count
        }
    
    async def get_vote_count(self, post_id: int) -> int:
        """获取帖子的投票计数
        
        Args:
            post_id: 帖子ID
            
        Returns:
            int: 投票计数
        """
        query = select(self.model.vote_count).where(self.model.id == post_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() or 0
    
    async def soft_delete(self, post_id: int) -> bool:
        """软删除帖子
        
        将帖子标记为已删除状态，而不是物理删除
        
        Args:
            post_id: 帖子ID
            
        Returns:
            bool: 操作是否成功
        """
        # 构建更新语句
        stmt = (
            update(self.model)
            .where(self.model.id == post_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        
        # 执行更新
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # 检查是否找到并更新了记录
        return result.rowcount > 0
    
    async def restore(self, post_id: int) -> bool:
        """恢复已删除的帖子
        
        将已删除的帖子恢复为正常状态
        
        Args:
            post_id: 帖子ID
            
        Returns:
            bool: 操作是否成功
        """
        # 构建更新语句
        stmt = (
            update(self.model)
            .where(
                and_(
                    self.model.id == post_id,
                    self.model.is_deleted == True
                )
            )
            .values(
                is_deleted=False,
                deleted_at=None,
                updated_at=datetime.now()
            )
        )
        
        # 执行更新
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # 检查是否找到并更新了记录
        return result.rowcount > 0 