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

from sqlalchemy import select, and_, func, update, insert, delete, desc, asc
# from sqlalchemy import select, and_, func, update, insert, delete, desc, asc
# from sqlalchemy import select, and_, or_, func, update, insert, delete, desc, asc
# from sqlalchemy.orm import joinedload
# from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.orm import joinedload, aliased
# from sqlalchemy.orm import selectinload, joinedload, aliased
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
# from typing import Dict, Any, List, Optional, Tuple
# from typing import Dict, Any, List, Optional, Tuple, Union

from .base_repository import BaseRepository
from ..models import Post, post_tags, PostVote, VoteType, Section, User
# from ..models import Post, post_tags, PostVote, VoteType, Category, Section, User
# from ..models import Post, Tag, post_tags, PostVote, VoteType, Category, User
# from ..models import Post, Tag, post_tags, PostVote, VoteType, Category, Section, User掉了掉了
from ...core.exceptions import BusinessError, BusinessException
from ..database import AsyncSessionLocal
import traceback
import json

# 定义帖子相关异常
class PostNotFoundError(BusinessError):
    """当指定的帖子不存在时抛出"""
    
    def __init__(self, message: str = "帖子不存在"):
        super().__init__(
            code="post_not_found",
            message=message,
            status_code=404
        )

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
        db = AsyncSessionLocal()
        try:
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
            result = await db.execute(query)
            post = result.unique().scalar_one_or_none()
            
            if not post:
                return None
                
            # 手动创建字典
            post_dict = {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "author_id": post.author_id,
                "section_id": post.section_id,
                "category_id": post.category_id,
                "is_hidden": post.is_hidden,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "is_deleted": post.is_deleted,
                "deleted_at": post.deleted_at,
                "vote_count": post.vote_count
            }
            
            # 添加关联实体信息
            if post.category:
                post_dict["category"] = {
                    "id": post.category.id,
                    "name": post.category.name,
                    "created_at": post.category.created_at
                }
                
            if post.section:
                post_dict["section"] = {
                    "id": post.section.id,
                    "name": post.section.name
                }
                
            if post.tags:
                post_dict["tags"] = [
                    {
                        "id": tag.id, 
                        "name": tag.name,
                        "created_at": tag.created_at
                    } for tag in post.tags
                ]
                
            return post_dict
        finally:
            await db.close()
    
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
        try:
            with open("logs/posts_repository_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 开始get_posts: skip={skip}, limit={limit}, include_hidden={include_hidden}\n")
            
            session = await self.get_session()
            try:
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
                
                with open("logs/posts_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 构建查询: {str(query)}\n")
                
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
                with open("logs/posts_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 执行查询\n")
                
                result = await session.execute(query)
                posts = result.unique().scalars().all()
                
                with open("logs/posts_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 查询结果: 获取到 {len(posts)} 条记录\n")
                
                # 构建计数查询
                count_query = (
                    select(func.count())
                    .select_from(self.model)
                    .where(and_(*conditions))
                )
                
                # 处理标签筛选
                if tag_ids:
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
                        count_query = count_query.where(subquery)
                        
                # 执行计数查询
                count_result = await session.execute(count_query)
                total = count_result.scalar_one()
                
                with open("logs/posts_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 计数结果: total={total}\n")
                
                # 处理结果
                posts_data = []
                for post in posts:
                    try:
                        post_dict = post.to_dict(include_relations=True) if hasattr(post, 'to_dict') else {
                            "id": post.id,
                            "title": post.title,
                            "content": post.content,
                            "author_id": post.author_id,
                            "section_id": post.section_id,
                            "category_id": post.category_id,
                            "is_hidden": post.is_hidden,
                            "created_at": post.created_at,
                            "updated_at": post.updated_at,
                            "is_deleted": post.is_deleted,
                            "vote_count": post.vote_count,
                            "category": {
                                "id": post.category.id, 
                                "name": post.category.name,
                                "created_at": post.category.created_at
                            } if post.category else None,
                            "section": {"id": post.section.id, "name": post.section.name} if post.section else None,
                            "tags": [{
                                "id": tag.id, 
                                "name": tag.name,
                                "created_at": tag.created_at
                            } for tag in post.tags]
                        }
                        
                        # 将datetime对象转换为ISO格式字符串，避免JSON序列化问题
                        if "created_at" in post_dict and post_dict["created_at"]:
                            post_dict["created_at"] = post_dict["created_at"].isoformat()
                        if "updated_at" in post_dict and post_dict["updated_at"]:
                            post_dict["updated_at"] = post_dict["updated_at"].isoformat()
                        
                        if "category" in post_dict and post_dict["category"] and "created_at" in post_dict["category"]:
                            if post_dict["category"]["created_at"]:
                                post_dict["category"]["created_at"] = post_dict["category"]["created_at"].isoformat()
                        
                        if "tags" in post_dict:
                            for tag in post_dict["tags"]:
                                if "created_at" in tag and tag["created_at"]:
                                    tag["created_at"] = tag["created_at"].isoformat()
                        
                        posts_data.append(post_dict)
                    except Exception as e:
                        with open("logs/posts_repository_debug.log", "a") as f:
                            f.write(f"{datetime.now().isoformat()} - 处理帖子数据错误, id={post.id}: {str(e)}\n")
                            f.write(f"错误堆栈: {traceback.format_exc()}\n")
                
                # 记录第一条数据的结构
                if posts_data and len(posts_data) > 0:
                    with open("logs/posts_repository_debug.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - 第一条帖子数据结构:\n")
                        f.write(json.dumps(posts_data[0], ensure_ascii=False, indent=2) + "\n")
                
                return posts_data, total
            except Exception as e:
                error_msg = f"获取帖子列表失败: {str(e)}"
                with open("logs/posts_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 错误: {error_msg}\n")
                    f.write(f"错误堆栈: {traceback.format_exc()}\n")
                raise
            finally:
                await session.close()
        except Exception as e:
            with open("logs/posts_repository_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - get_posts发生异常: {str(e)}\n")
                f.write(f"错误堆栈: {traceback.format_exc()}\n")
            raise
    
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
        try:
            async with self.session() as session:
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
                result = await session.execute(stmt)
                await session.commit()
                
                # 检查是否找到并更新了记录
                return result.rowcount > 0
        except Exception as e:
            with open("logs/post_visibility_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 切换帖子可见性异常: {str(e)}\n")
                f.write(f"错误堆栈: {traceback.format_exc()}\n")
            return False
    
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
    
    async def vote_post(self, post_id: int, user_id: int, vote_type: VoteType):
        """为帖子投票
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            vote_type: 投票类型
            
        Returns:
            dict: 投票结果，包含投票计数和用户的投票状态
        """
        try:
            with open("logs/vote_repository_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - vote_post开始执行: post_id={post_id}, user_id={user_id}, vote_type={vote_type}\n")
            
            # 使用BaseRepository的session上下文管理器
            async with self.session() as session:
                # 首先检查帖子是否存在
                post_query = select(self.model).where(
                    and_(
                        self.model.id == post_id,
                        self.model.is_deleted == False
                    )
                )
                
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 执行查询: {str(post_query)}\n")
                
                post_result = await session.execute(post_query)
                post = post_result.scalar_one_or_none()
                
                if not post:
                    with open("logs/vote_repository_debug.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - 帖子不存在或已删除: post_id={post_id}\n")
                    return None
                
                # 查询用户的现有投票记录
                vote_query = select(PostVote).where(
                    and_(
                        PostVote.post_id == post_id,
                        PostVote.user_id == user_id
                    )
                )
                
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 执行查询: {str(vote_query)}\n")
                
                vote_result = await session.execute(vote_query)
                existing_vote = vote_result.scalar_one_or_none()
                
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 查询结果: existing_vote={existing_vote}\n")
                
                if existing_vote:
                    # 如果已投票且投票类型相同，则移除投票（取消投票）
                    if existing_vote.vote_type == vote_type.value:
                        delete_query = delete(PostVote).where(
                            and_(
                                PostVote.post_id == post_id,
                                PostVote.user_id == user_id
                            )
                        )
                        with open("logs/vote_repository_debug.log", "a") as f:
                            f.write(f"{datetime.now().isoformat()} - 执行删除: {str(delete_query)}\n")
                            
                        await session.execute(delete_query)
                        action = "removed"
                    else:
                        # 如果已投票但投票类型不同，则更新投票类型
                        update_query = (
                            update(PostVote)
                            .where(
                                and_(
                                    PostVote.post_id == post_id,
                                    PostVote.user_id == user_id
                                )
                            )
                            .values(vote_type=vote_type.value)
                        )
                        with open("logs/vote_repository_debug.log", "a") as f:
                            f.write(f"{datetime.now().isoformat()} - 执行更新: {str(update_query)}\n")
                            
                        await session.execute(update_query)
                        action = "updated"
                else:
                    # 如果尚未投票，则创建新投票
                    insert_query = insert(PostVote).values(
                        post_id=post_id,
                        user_id=user_id,
                        vote_type=vote_type.value,
                        created_at=datetime.now()
                    )
                    with open("logs/vote_repository_debug.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - 执行插入: {str(insert_query)}\n")
                        
                    await session.execute(insert_query)
                    action = "added"
                
                # 获取最新的投票统计
                upvotes_query = select(func.count()).select_from(PostVote).where(
                    and_(
                        PostVote.post_id == post_id,
                        PostVote.vote_type == VoteType.UPVOTE.value
                    )
                )
                downvotes_query = select(func.count()).select_from(PostVote).where(
                    and_(
                        PostVote.post_id == post_id,
                        PostVote.vote_type == VoteType.DOWNVOTE.value
                    )
                )
                
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 执行统计查询\n")
                
                upvotes_result = await session.execute(upvotes_query)
                downvotes_result = await session.execute(downvotes_query)
                
                upvotes_count = upvotes_result.scalar() or 0
                downvotes_count = downvotes_result.scalar() or 0
                
                # 更新帖子的投票计数
                update_post_query = (
                    update(self.model)
                    .where(self.model.id == post_id)
                    .values(
                        vote_count=upvotes_count - downvotes_count,
                        updated_at=datetime.now()
                    )
                )
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - 执行更新帖子: {str(update_post_query)}\n")
                
                try:
                    await session.execute(update_post_query)
                    await session.commit()
                    
                    with open("logs/vote_repository_debug.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - 提交事务成功\n")
                except Exception as e:
                    with open("logs/vote_repository_debug.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - 更新帖子失败: {str(e)}\n")
                    # 继续执行，返回投票结果，但不更新帖子计数
                
                result = {
                    "post_id": post_id,
                    "upvotes": upvotes_count,
                    "downvotes": downvotes_count,
                    "score": upvotes_count - downvotes_count,
                    "user_vote": None if action == "removed" else vote_type.value,
                    "action": action
                }
                
                with open("logs/vote_repository_debug.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - vote_post完成, 返回结果: {json.dumps(result, default=str)}\n")
                
                return result
        except Exception as e:
            with open("logs/vote_repository_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - vote_post发生异常: {str(e)}\n")
                f.write(f"错误堆栈: {traceback.format_exc()}\n")
            raise
    
    async def get_vote_count(self, post_id: int) -> int:
        """获取帖子的投票计数
        
        Args:
            post_id: 帖子ID
            
        Returns:
            int: 投票计数
        """
        try:
            async with self.session() as session:
                query = select(self.model.vote_count).where(self.model.id == post_id)
                result = await session.execute(query)
                return result.scalar_one_or_none() or 0
        except Exception as e:
            with open("logs/vote_count_debug.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 获取投票计数异常: {str(e)}\n")
                f.write(f"错误堆栈: {traceback.format_exc()}\n")
            return 0
    
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