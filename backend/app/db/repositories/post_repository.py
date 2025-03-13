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
from sqlalchemy.orm import joinedload, aliased
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .base_repository import BaseRepository
from ..models import Post, PostVote, VoteType, Section, Category , User, Tag
from ..models.post_tag import post_tags  # 正确导入post_tags表
from ...core.exceptions import BusinessError
from ..database import AsyncSessionLocal, async_get_db
import traceback
import json
import logging

logger = logging.getLogger(__name__)



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
        try:
            logger.info(f"开始获取帖子关联信息，ID: {post_id}, include_hidden: {include_hidden}")
            
            async with async_get_db() as db:
                # 构建查询条件
                conditions = [self.model.id == post_id, self.model.is_deleted == False]
                if not include_hidden:
                    conditions.append(self.model.is_hidden == False)
                
                logger.info(f"查询条件: {conditions}")
                
                # 构建查询，加载关联实体
                query = (
                    select(self.model)
                    .options(
                        joinedload(self.model.category),
                        joinedload(self.model.section),
                        joinedload(self.model.tags),
                        joinedload(self.model.author)
                    )
                    .where(and_(*conditions))
                )
                
                # 执行查询
                try:
                    result = await db.execute(query)
                    post = result.unique().scalar_one_or_none()
                    
                    if not post:
                        logger.warning(f"未找到帖子，ID: {post_id}")
                        return None
                        
                    logger.info(f"找到帖子，ID: {post_id}")
                    post_dict = self.model_to_dict(post)
                    
                    # 添加关联实体信息
                    if post.category:
                        logger.info(f"处理分类信息，ID: {post.category_id}")
                        category_dict = {
                            "id": post.category.id,
                            "name": post.category.name,
                            "description": post.category.description or "",
                            "created_at": post.category.created_at.isoformat() if hasattr(post.category.created_at, 'isoformat') else post.category.created_at
                        }
                        post_dict["category"] = category_dict
                    else:
                        logger.info(f"帖子没有关联分类，ID: {post_id}")
                        post_dict["category"] = None
                        
                    if post.section:
                        logger.info(f"处理版块信息，ID: {post.section_id}")
                        section_dict = {
                            "id": post.section.id,
                            "name": post.section.name,
                            "description": post.section.description or "",
                            "created_at": post.section.created_at.isoformat() if hasattr(post.section.created_at, 'isoformat') else post.section.created_at
                        }
                        post_dict["section"] = section_dict
                    else:
                        logger.info(f"帖子没有关联版块，ID: {post_id}")
                        post_dict["section"] = None
                    
                    # 不要直接访问post.comments，而是设置为空列表
                    logger.info(f"设置评论为空列表，ID: {post_id}")
                    post_dict["comments"] = []
                        
                    # 确保标签列表始终存在
                    if post.tags:
                        logger.info(f"处理标签信息，数量: {len(post.tags)}")
                        post_dict["tags"] = [{
                            "id": tag.id,
                            "name": tag.name,
                            "created_at": tag.created_at.isoformat() if hasattr(tag.created_at, 'isoformat') else tag.created_at,
                            "post_count": tag.post_count if hasattr(tag, 'post_count') else 0
                        } for tag in post.tags]
                    else:
                        logger.info(f"帖子没有标签，ID: {post_id}")
                        post_dict["tags"] = []
                        
                    # 添加作者信息
                    if post.author:
                        logger.info(f"处理作者信息，ID: {post.author_id}")
                        author_dict = {
                            "id": post.author.id,
                            "username": post.author.username,
                            "avatar_url": post.author.avatar_url,
                            "role": post.author.role
                        }
                        post_dict["author"] = author_dict
                    else:
                        logger.info(f"帖子没有作者信息，ID: {post_id}")
                        post_dict["author"] = None
                        
                    logger.info(f"成功获取帖子关联信息，ID: {post_id}")
                    return post_dict
                except Exception as query_error:
                    logger.error(f"执行查询失败，ID: {post_id}, 错误: {str(query_error)}", exc_info=True)
                    return None
        except Exception as e:
            logger.error(f"获取帖子关联信息失败，ID: {post_id}, 错误: {str(e)}", exc_info=True)
            return None
    
    async def get_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        filter_options: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取帖子列表
        
        Args:
            skip: 分页偏移
            limit: 每页数量
            filter_options: 过滤条件字典，支持按作者、分类、版块等筛选
            sort_by: 排序字段
            sort_order: 排序方向
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        try:
            logger.info(f"开始获取帖子列表：skip={skip}, limit={limit}, filter_options={filter_options}")
            
            async with async_get_db() as db:
                # 构建查询
                query = select(Post).options(
                    joinedload(Post.category),
                    joinedload(Post.section),
                    joinedload(Post.tags),
                    joinedload(Post.author)
                )
                
                # 应用过滤条件
                if filter_options:
                    logger.info(f"应用过滤条件: {filter_options}")
                    if "author_id" in filter_options:
                        query = query.where(Post.author_id == filter_options["author_id"])
                    
                    if "category_id" in filter_options:
                        query = query.where(Post.category_id == filter_options["category_id"])
                    
                    if "section_id" in filter_options:
                        query = query.where(Post.section_id == filter_options["section_id"])
                    
                    # 处理标签筛选
                    if "tag_ids" in filter_options and filter_options["tag_ids"]:
                        # 使用子查询找出包含指定标签的帖子ID
                        tag_ids = filter_options["tag_ids"]
                        logger.info(f"应用标签过滤: {tag_ids}")
                        tag_query = (
                            select(post_tags.c.post_id)
                            .where(post_tags.c.tag_id.in_(tag_ids))
                            .distinct()
                        )
                        tag_results = await db.execute(tag_query)
                        post_ids = [row[0] for row in tag_results.all()]
                        
                        if post_ids:
                            logger.info(f"找到包含标签的帖子IDs: {post_ids}")
                            query = query.where(Post.id.in_(post_ids))
                        else:
                            # 如果没有包含这些标签的帖子，返回空列表
                            logger.info("没有找到包含指定标签的帖子，返回空列表")
                            return [], 0
                    
                    # 只获取未删除的帖子，除非特别指定
                    if filter_options.get("include_deleted", False) is False:
                        query = query.where(Post.is_deleted == False)
                    
                    # 处理隐藏帖子的查询逻辑
                    if "include_hidden" in filter_options:
                        # 如果include_hidden为True，不添加任何条件（即显示所有帖子，包括隐藏的）
                        if not filter_options["include_hidden"]:
                            # 如果为False，只显示未隐藏的帖子
                            query = query.where(Post.is_hidden == False)
                    else:
                        # 默认情况下，只显示未隐藏的帖子
                        query = query.where(Post.is_hidden == False)
                else:
                    # 默认只获取未删除和未隐藏的帖子
                    logger.info("使用默认过滤条件: 未删除且未隐藏")
                    query = query.where(Post.is_deleted == False)
                    query = query.where(Post.is_hidden == False)
                
                # 应用排序
                if sort_by:
                    logger.info(f"应用排序: {sort_by} {sort_order}")
                    if hasattr(Post, sort_by):
                        sort_column = getattr(Post, sort_by)
                        if sort_order and sort_order.lower() == "asc":
                            query = query.order_by(asc(sort_column))
                        else:
                            query = query.order_by(desc(sort_column))
                    else:
                        logger.warning(f"排序字段 {sort_by} 不存在，使用默认排序")
                        query = query.order_by(desc(Post.created_at))
                else:
                    # 默认按创建时间倒序排序
                    query = query.order_by(desc(Post.created_at))
                
                # 查询总数
                count_query = select(func.count(Post.id))
                for clause in query.whereclause.clauses if hasattr(query, 'whereclause') and hasattr(query.whereclause, 'clauses') else []:
                    count_query = count_query.where(clause)
                
                count_result = await db.execute(count_query)
                total = count_result.scalar() or 0
                
                logger.info(f"查询到的帖子总数: {total}")
                
                # 应用分页
                query = query.offset(skip).limit(limit)
                
                # 执行查询
                result = await db.execute(query)
                # 使用unique()确保关系实体正确去重
                posts = result.unique().scalars().all()
                
                logger.info(f"查询到 {len(posts)} 条帖子")
                
                # 转换为字典
                post_dicts = []
                for post in posts:
                    try:
                        post_dict = self.model_to_dict(post)
                        
                        # 添加分类信息
                        if post.category:
                            category_dict = {
                                "id": post.category.id,
                                "name": post.category.name,
                                "description": post.category.description or "",
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
                                "description": post.section.description or "",
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
                        
                        # 添加作者信息
                        if post.author:
                            logger.info(f"处理作者信息，ID: {post.author_id}")
                            author_dict = {
                                "id": post.author.id,
                                "username": post.author.username,
                                "avatar_url": post.author.avatar_url,
                                "role": post.author.role
                            }
                            post_dict["author"] = author_dict
                        else:
                            post_dict["author"] = None
                        
                        post_dict["comments"] = None
                        
                        # 添加到结果列表
                        post_dicts.append(post_dict)
                    except Exception as e:
                        logger.error(f"处理帖子 {post.id} 失败: {str(e)}", exc_info=True)
                        # 继续处理下一个帖子
                
                logger.info(f"成功处理 {len(post_dicts)}/{len(posts)} 条帖子")
                return post_dicts, total
        except Exception as e:
            logger.error(f"获取帖子列表失败: {str(e)}", exc_info=True)
            return [], 0
    
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
            # 确保帖子存在
            post = await self.get(post_id)
            if not post:
                logger.error(f"更新标签失败：帖子不存在，ID: {post_id}")
                return False
            
            # 过滤掉无效的标签ID（必须是有效的整数）
            filtered_tag_ids = []
            for tag_id in tag_ids:
                try:
                    filtered_tag_ids.append(int(tag_id))
                except (ValueError, TypeError):
                    logger.warning(f"忽略无效的标签ID: {tag_id}")
            
            logger.info(f"为帖子 {post_id} 更新标签: {filtered_tag_ids}")
            
            async with async_get_db() as db:
                # 开始事务
                async with db.begin():
                    # 删除所有现有的标签关联
                    delete_stmt = delete(post_tags).where(post_tags.c.post_id == post_id)
                    await db.execute(delete_stmt)
                    
                    # 如果标签ID列表为空，只删除不添加
                    if not filtered_tag_ids:
                        logger.info(f"已清除帖子 {post_id} 的所有标签关联")
                        return True
                    
                    # 插入新的标签关联
                    success_count = 0
                    for tag_id in filtered_tag_ids:
                        try:
                            # 验证标签是否存在
                            tag_check = await db.execute(
                                select(Tag).where(
                                    (Tag.id == tag_id) & 
                                    (Tag.is_deleted == False)
                                )
                            )
                            tag = tag_check.scalar_one_or_none()
                            
                            if not tag:
                                logger.warning(f"标签不存在或已删除，ID: {tag_id}")
                                continue
                            
                            # 插入关联
                            insert_stmt = insert(post_tags).values(post_id=post_id, tag_id=tag_id)
                            await db.execute(insert_stmt)
                            success_count += 1
                            
                            # 更新标签统计信息
                            try:
                                tag.post_count = tag.post_count + 1 if tag.post_count else 1
                                tag.last_used_at = datetime.now()
                                db.add(tag)
                            except Exception as stats_error:
                                logger.warning(f"更新标签统计信息失败: {str(stats_error)}")
                                # 不影响主要流程
                                
                        except Exception as tag_error:
                            logger.warning(f"插入标签 {tag_id} 关联失败: {str(tag_error)}")
                            # 继续处理下一个标签
                
                if success_count > 0:
                    logger.info(f"成功为帖子 {post_id} 关联 {success_count}/{len(filtered_tag_ids)} 个标签")
                    return True
                else:
                    logger.warning(f"未能为帖子 {post_id} 关联任何标签")
                    return False
                
        except Exception as e:
            logger.error(f"更新帖子标签失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            return False
    
    async def toggle_visibility(self, post_id: int, is_hidden: bool) -> bool:
        """切换帖子可见性
        
        Args:
            post_id: 帖子ID
            is_hidden: 是否隐藏
            
        Returns:
            bool: 操作是否成功
        """
        try:
            async with async_get_db() as db:
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
                result = await db.execute(stmt)
                await db.commit()
                
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
        result = await async_get_db().execute(query)
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
            
            # 使用BaseRepository的session上下文管理器
            async with async_get_db() as db:
                # 首先检查帖子是否存在
                post_query = select(self.model).where(
                    and_(
                        self.model.id == post_id,
                        self.model.is_deleted == False
                    )
                )
                
                post_result = await db.execute(post_query)
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
                
                vote_result = await db.execute(vote_query)
                existing_vote = vote_result.scalar_one_or_none()
                
                if existing_vote:
                    # 如果已投票且投票类型相同，则移除投票（取消投票）
                    if existing_vote.vote_type == vote_type.value:
                        delete_query = delete(PostVote).where(
                            and_(
                                PostVote.post_id == post_id,
                                PostVote.user_id == user_id
                            )
                        )
                            
                        await db.execute(delete_query)
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
                            
                        await db.execute(update_query)
                        action = "updated"
                else:
                    # 如果尚未投票，则创建新投票
                    insert_query = insert(PostVote).values(
                        post_id=post_id,
                        user_id=user_id,
                        vote_type=vote_type.value,
                        created_at=datetime.now()
                    )
                        
                    await db.execute(insert_query)
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
                
                upvotes_result = await db.execute(upvotes_query)
                downvotes_result = await db.execute(downvotes_query)
                
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
                
                try:
                    await db.execute(update_post_query)
                    await db.commit()
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
            async with async_get_db() as db:
                query = select(self.model.vote_count).where(self.model.id == post_id)
                result = await db.execute(query)
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
        try:
            async with async_get_db() as db:
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
                result = await db.execute(stmt)
                await db.commit()
                
                # 检查是否找到并更新了记录
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"软删除帖子失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            return False
    
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
        result = await async_get_db().execute(stmt)
        await async_get_db().commit()
        
        # 检查是否找到并更新了记录
        return result.rowcount > 0
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建帖子
        
        覆盖基类的create方法，处理标签关联
        
        Args:
            data: 帖子数据，可能包含tag_ids字段
            
        Returns:
            Dict[str, Any]: 创建的帖子数据
        """
        # 提取标签ID列表，不是Post模型的直接字段
        tag_ids = data.pop("tag_ids", []) if "tag_ids" in data else []
        
        # 确保tag_ids是列表且值为整数
        if tag_ids is not None and not isinstance(tag_ids, list):
            tag_ids = []
        elif tag_ids:  # 如果有标签ID，确保都是整数
            filtered_tag_ids = []
            for tag_id in tag_ids:
                try:
                    filtered_tag_ids.append(int(tag_id))
                except (ValueError, TypeError):
                    logger.warning(f"忽略无效的标签ID: {tag_id}")
            tag_ids = filtered_tag_ids
            
        logger.info(f"创建帖子，标签ID: {tag_ids}")
        
        # 创建帖子
        async with async_get_db() as db:
            try:
                # 创建帖子实例
                post = Post(**data)
                db.add(post)
                await db.flush()  # 刷新以获取ID
                
                post_id = post.id
                logger.info(f"成功创建帖子，ID: {post_id}")
                
                # 关联标签
                if tag_ids:
                    success_count = 0
                    for tag_id in tag_ids:
                        try:
                            # 验证标签是否存在
                            tag_check = await db.execute(
                                select(Tag).where(
                                    (Tag.id == tag_id) & 
                                    (Tag.is_deleted == False)
                                )
                            )
                            tag = tag_check.scalar_one_or_none()
                            
                            if not tag:
                                logger.warning(f"标签不存在或已删除，ID: {tag_id}")
                                continue
                            
                            # 插入关联
                            insert_stmt = insert(post_tags).values(post_id=post_id, tag_id=tag_id)
                            await db.execute(insert_stmt)
                            success_count += 1
                            
                            # 更新标签统计信息
                            tag.post_count = tag.post_count + 1 if tag.post_count else 1
                            tag.last_used_at = datetime.now()
                            db.add(tag)
                        except Exception as tag_error:
                            logger.warning(f"插入标签 {tag_id} 关联失败: {str(tag_error)}")
                            # 继续处理下一个标签
                
                # 提交事务
                await db.commit()
                await db.refresh(post)
                
                # 获取完整的帖子信息，包含标签
                post_dict = self.model_to_dict(post)
                
                # 添加标签信息
                if tag_ids:
                    post_with_tags = await self.get_with_relations(post_id)
                    if post_with_tags and "tags" in post_with_tags:
                        post_dict["tags"] = post_with_tags["tags"]
                    else:
                        post_dict["tags"] = []
                else:
                    post_dict["tags"] = []
                
                return post_dict
                
            except Exception as e:
                await db.rollback()
                logger.error(f"创建帖子失败: {str(e)}", exc_info=True)
                raise e 