from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc
from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import relationship

from ..models.section import Section
from ..models.user import User
from ..models.section_moderator import SectionModerator
from ..models.post import Post
from ..models.category import Category
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException
# from ...core.database import async_get_db
from ...schemas.responses.section import (
    SectionResponse, 
    SectionDetailResponse,
    SectionListResponse,
    SectionStatsResponse
)
import logging
from ...core.logging import logging

logger = logging.getLogger(__name__)

class SectionRepository(BaseRepository):
    """版块仓库
    
    提供版块相关的数据库访问方法，包括查询、创建、更新和删除版块，以及版主管理。
    """
    
    def __init__(self):
        """初始化版块仓库"""
        super().__init__(Section)
    
    async def get_by_id(self, section_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """根据ID获取版块
        
        Args:
            section_id: 版块ID
            include_deleted: 是否包含已删除的版块
            
        Returns:
            Optional[Dict[str, Any]]: 版块信息字典，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = select(Section).where(Section.id == section_id)
            
            if not include_deleted:
                query = query.where(Section.is_deleted == False)
                
            result = await db.execute(query)
            section = result.scalar_one_or_none()
            
            if section is None:
                return None
                
            return self.model_to_dict(section)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有版块
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 版块列表和总数
        """
        async with self.async_get_db() as db:
            # 查询版块，不包括已删除的
            query = (
                select(Section)
                .where(Section.is_deleted == False)
                .offset(skip)
                .limit(limit)
            )
            
            result = await db.execute(query)
            sections = result.scalars().all()
            
            # 查询总数
            count_query = select(func.count(Section.id)).where(Section.is_deleted == False)
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            sections_list = [self.model_to_dict(section) for section in sections]
                
            return sections_list, total
    
    async def create(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建版块
        
        Args:
            section_data: 版块数据
            
        Returns:
            Dict[str, Any]: 创建的版块
        """
        async with self.async_get_db() as db:
            # 检查版块名称是否已存在
            name_query = select(Section).where(
                Section.name == section_data["name"],
                Section.is_deleted == False
            )
            name_result = await db.execute(name_query)
            existing = name_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="SECTION_EXISTS",
                    message="版块名称已存在"
                )
            
            # 创建版块
            section = Section(**section_data)
            db.add(section)
            await db.commit()
            await db.refresh(section)
            
            # 返回创建的版块
            return self.model_to_dict(section)
    
    async def update(self, section_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新版块
        
        Args:
            section_id: 版块ID
            data: 要更新的数据
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的版块，不存在则返回None
        """
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                return None
            
            # 如果更新名称，检查是否重复
            if "name" in data and data["name"] != section.name:
                name_query = select(Section).where(
                    Section.name == data["name"],
                    Section.is_deleted == False
                )
                name_result = await db.execute(name_query)
                existing = name_result.scalar_one_or_none()
                
                if existing is not None:
                    raise BusinessException(
                        status_code=400,
                        error_code="SECTION_EXISTS",
                        message="版块名称已存在"
                    )
            
            # 更新版块
            for key, value in data.items():
                if hasattr(section, key) and key != "id":
                    setattr(section, key, value)
            
            await db.commit()
            await db.refresh(section)
            
            # 返回更新后的版块
            return self.model_to_dict(section)
    
    async def soft_delete(self, section_id: int) -> bool:
        """软删除版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 查询版块
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                return False
                
            # 检查是否有关联的未删除帖子
            posts_query = select(func.count(Post.id)).where(
                Post.section_id == section_id,
                Post.is_deleted == False
            )
            posts_result = await db.execute(posts_query)
            post_count = posts_result.scalar() or 0
            
            if post_count > 0:
                # 有关联帖子，可以继续删除版块，但要记录警告日志
                # 这里不阻止删除，因为帖子仍然可以访问，只是不会显示在版块页面
                pass
            
            # 软删除版块
            section.is_deleted = True
            if hasattr(section, "deleted_at"):
                section.deleted_at = datetime.now()
            
            await db.commit()
            return True
    
    async def restore(self, section_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的版块，如果版块不存在或未被删除则返回None
        """
        async with self.async_get_db() as db:
            # 查询版块
            section = await db.get(Section, section_id)
            if not section:
                return None
            
            # 如果版块未被删除，则无需恢复
            if not section.is_deleted:
                raise BusinessException(
                    status_code=400,
                    error_code="SECTION_NOT_DELETED",
                    message="版块未被删除"
                )
            
            # 恢复版块
            section.is_deleted = False
            section.deleted_at = None
            
            await db.commit()
            await db.refresh(section)
            
            # 返回恢复后的版块
            return self.model_to_dict(section)
    
    async def add_moderator(self, section_id: int, user_id: int) -> bool:
        """添加版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
            
            # 检查用户是否存在
            user = await db.get(User, user_id)
            if not user:
                raise BusinessException(
                    status_code=404,
                    error_code="USER_NOT_FOUND",
                    message="用户不存在"
                )
            
            # 检查是否已经是版主
            moderator_query = select(SectionModerator).where(
                SectionModerator.section_id == section_id,
                SectionModerator.user_id == user_id,
                SectionModerator.is_deleted == False
            )
            moderator_result = await db.execute(moderator_query)
            existing_moderator = moderator_result.scalar_one_or_none()
            
            if existing_moderator is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="ALREADY_MODERATOR",
                    message="该用户已是此版块的版主"
                )
            
            # 检查是否存在已删除的记录
            deleted_query = select(SectionModerator).where(
                SectionModerator.section_id == section_id,
                SectionModerator.user_id == user_id,
                SectionModerator.is_deleted == True
            )
            deleted_result = await db.execute(deleted_query)
            deleted_record = deleted_result.scalar_one_or_none()
            
            if deleted_record:
                # 恢复已删除的记录
                deleted_record.is_deleted = False
            else:
                # 创建新记录
                moderator = SectionModerator(section_id=section_id, user_id=user_id)
                db.add(moderator)
            
            # 更新用户角色为版主（如果不是管理员）
            if user.role not in ["admin", "super_admin", "moderator"]:
                user.role = "moderator"
            
            await db.commit()
            return True
    
    async def remove_moderator(self, section_id: int, user_id: int) -> bool:
        """移除版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
            
            # 检查是否是版主
            moderator_query = select(SectionModerator).where(
                SectionModerator.section_id == section_id,
                SectionModerator.user_id == user_id,
                SectionModerator.is_deleted == False
            )
            moderator_result = await db.execute(moderator_query)
            moderator = moderator_result.scalar_one_or_none()
            
            if moderator is None:
                raise BusinessException(
                    status_code=404,
                    error_code="NOT_MODERATOR",
                    message="该用户不是此版块的版主"
                )
            
            # 软删除版主记录
            moderator.is_deleted = True
            
            # 检查用户是否还是其他版块的版主
            other_sections_query = select(func.count(SectionModerator.section_id)).where(
                SectionModerator.user_id == user_id,
                SectionModerator.section_id != section_id,
                SectionModerator.is_deleted == False
            )
            other_sections_result = await db.execute(other_sections_query)
            other_sections_count = other_sections_result.scalar() or 0
            
            # 如果不是其他版块的版主，且不是管理员，则更新角色为普通用户
            if other_sections_count == 0:
                user = await db.get(User, user_id)
                if user and user.role == "moderator":
                    user.role = "user"
            
            await db.commit()
            return True
    
    async def restore_moderator(self, section_id: int, user_id: int) -> bool:
        """恢复版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
            
            # 检查用户是否存在
            user = await db.get(User, user_id)
            if not user:
                raise BusinessException(
                    status_code=404,
                    error_code="USER_NOT_FOUND",
                    message="用户不存在"
                )
            
            # 检查版主记录是否存在且已删除
            moderator_query = select(SectionModerator).where(
                SectionModerator.section_id == section_id,
                SectionModerator.user_id == user_id
            )
            moderator_result = await db.execute(moderator_query)
            moderator = moderator_result.scalar_one_or_none()
            
            if moderator is None:
                raise BusinessException(
                    status_code=404,
                    error_code="MODERATOR_NOT_FOUND",
                    message="未找到相关版主记录"
                )
            
            if not moderator.is_deleted:
                raise BusinessException(
                    status_code=400,
                    error_code="ALREADY_MODERATOR",
                    message="该用户已是此版块的版主"
                )
            
            # 恢复版主记录
            moderator.is_deleted = False
            
            # 更新用户角色为版主（如果不是管理员）
            if user.role not in ["admin", "super_admin", "moderator"]:
                user.role = "moderator"
            
            await db.commit()
            return True
    
    async def get_section_posts(self, section_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取版块下的帖子
        
        Args:
            section_id: 版块ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
        """
        from ..models.post_tag import post_tags
        
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    code="SECTION_NOT_FOUND",
                    message="版块不存在",
                    status_code=404
                )
            
            # 查询帖子
            posts_query = (
                select(Post)
                .where(
                    Post.section_id == section_id,
                    Post.is_deleted == False
                )
                .order_by(desc(Post.created_at))
                .offset(skip)
                .limit(limit)
            )
            posts_result = await db.execute(posts_query)
            posts = posts_result.unique().scalars().all()
            
            # 查询总数
            count_query = select(func.count(Post.id)).where(
                Post.section_id == section_id,
                Post.is_deleted == False
            )
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 处理结果
            posts_list = []
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
                    
                    post_dict["comments"] = None
                    posts_list.append(post_dict)
                except Exception as e:
                    # 记录错误但继续处理其他帖子
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"处理帖子 {post.id} 失败: {str(e)}", exc_info=True)
                    continue
            
            return posts_list, total
    
    async def get_moderators(self, section_id: int) -> List[Dict[str, Any]]:
        """获取版块的版主列表
        
        Args:
            section_id: 版块ID
            
        Returns:
            List[Dict[str, Any]]: 版主用户列表
        
        Raises:
            BusinessException: 当版块不存在时抛出业务异常
        """
        async with self.async_get_db() as db:
            # 检查版块是否存在
            section = await db.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
                
            # 查询版主
            query = (
                select(User)
                .join(SectionModerator, User.id == SectionModerator.user_id)
                .where(
                    SectionModerator.section_id == section_id,
                    SectionModerator.is_deleted == False,
                    User.is_deleted == False
                )
            )
            
            result = await db.execute(query)
            moderators = result.scalars().all()
            
            # 返回版主列表
            return [
                {
                    "id": moderator.id,
                    "username": moderator.username,
                    "nickname": moderator.nickname if hasattr(moderator, "nickname") else None,
                    "avatar": moderator.avatar if hasattr(moderator, "avatar") else None,
                    "role": moderator.role
                }
                for moderator in moderators
            ] 

    async def get_sections(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        include_post_count: bool = False
    ) -> Tuple[List[SectionResponse], int]:
        """获取版块列表
        
        Args:
            skip: 分页偏移量
            limit: 每页数量
            category_id: 分类ID过滤
            include_post_count: 是否包含帖子数量
            
        Returns:
            Tuple[List[SectionResponse], int]: 版块列表和总数
        """
        # 构建查询条件
        conditions = [Section.is_deleted == False]
        
        # 如果指定了分类ID，添加过滤条件
        if category_id is not None:
            conditions.append(Section.category_id == category_id)
        
        async with self.async_get_db() as db:
            try:
                # 构建查询
                query = select(Section).where(and_(*conditions))
                
                # 排序：按照排序值和名称排序
                query = query.order_by(Section.sort_order, Section.name)
                
                # 获取总数
                count_query = select(func.count()).select_from(query.subquery())
                count_result = await db.execute(count_query)
                total = count_result.scalar_one() or 0
                
                # 应用分页
                query = query.offset(skip).limit(limit)
                
                # 执行查询
                result = await db.execute(query)
                sections = result.scalars().all()
                
                # 转换为响应对象
                section_responses = []
                for section in sections:
                    section_dict = {c.name: getattr(section, c.name) for c in section.__table__.columns}
                    
                    # 如果需要包含帖子数量
                    if include_post_count:
                        posts_count_query = select(func.count()).select_from(Post).where(
                            and_(
                                Post.section_id == section.id,
                                Post.is_deleted == False
                            )
                        )
                        posts_count_result = await db.execute(posts_count_query)
                        posts_count = posts_count_result.scalar_one() or 0
                        section_dict["posts_count"] = posts_count
                    
                    section_responses.append(SectionResponse(**section_dict))
                
                return section_responses, total
            except Exception as e:
                logger.error(f"获取版块列表失败: {str(e)}")
                return [], 0

    async def get_section_detail(self, section_id: int) -> Optional[SectionDetailResponse]:
        """获取版块详情
        
        Args:
            section_id: 版块ID
            
        Returns:
            Optional[SectionDetailResponse]: 版块详情，不存在则返回None
        """
        async with self.async_get_db() as db:
            try:
                # 获取版块
                result = await db.execute(
                    select(Section).where(
                        and_(
                            Section.id == section_id,
                            Section.is_deleted == False
                        )
                    )
                )
                section = result.scalar_one_or_none()
                
                if not section:
                    return None
                
                # 获取该版块下的帖子数量
                posts_count_query = select(func.count()).select_from(Post).where(
                    and_(
                        Post.section_id == section_id,
                        Post.is_deleted == False
                    )
                )
                posts_count_result = await db.execute(posts_count_query)
                posts_count = posts_count_result.scalar_one() or 0
                
                # 获取所属分类信息
                category_info = None
                if section.category_id:
                    category_query = select(Category).where(
                        and_(
                            Category.id == section.category_id,
                            Category.is_deleted == False
                        )
                    )
                    category_result = await db.execute(category_query)
                    category = category_result.scalar_one_or_none()
                    
                    if category:
                        category_info = {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description
                        }
                
                # 转换为响应对象
                section_dict = {c.name: getattr(section, c.name) for c in section.__table__.columns}
                section_dict["posts_count"] = posts_count
                section_dict["category"] = category_info
                
                return SectionDetailResponse(**section_dict)
            except Exception as e:
                logger.error(f"获取版块详情失败: {str(e)}")
                return None

    async def create_section(self, data: Dict[str, Any]) -> Optional[SectionResponse]:
        """创建版块
        
        Args:
            data: 版块数据
            
        Returns:
            Optional[SectionResponse]: 创建的版块，失败则返回None
        """
        async with self.async_get_db() as db:
            try:
                # 验证分类是否存在
                if "category_id" in data and data["category_id"]:
                    category_query = select(Category).where(
                        and_(
                            Category.id == data["category_id"],
                            Category.is_deleted == False
                        )
                    )
                    category_result = await db.execute(category_query)
                    category = category_result.scalar_one_or_none()
                    
                    if not category:
                        logger.warning(f"创建版块失败: 分类不存在，ID={data['category_id']}")
                        return None
                
                # 创建版块
                section = Section(**data)
                db.add(section)
                await db.commit()
                await db.refresh(section)
                
                # 转换为响应对象
                section_dict = {c.name: getattr(section, c.name) for c in section.__table__.columns}
                return SectionResponse(**section_dict)
            except Exception as e:
                await db.rollback()
                logger.error(f"创建版块失败: {str(e)}")
                return None

    async def update_section(
        self, 
        section_id: int, 
        data: Dict[str, Any]
    ) -> Optional[SectionResponse]:
        """更新版块
        
        Args:
            section_id: 版块ID
            data: 更新数据
            
        Returns:
            Optional[SectionResponse]: 更新后的版块，失败则返回None
        """
        async with self.async_get_db() as db:
            try:
                # 获取版块
                result = await db.execute(
                    select(Section).where(
                        and_(
                            Section.id == section_id,
                            Section.is_deleted == False
                        )
                    )
                )
                section = result.scalar_one_or_none()
                
                if not section:
                    return None
                
                # 如果更新分类ID，验证分类是否存在
                if "category_id" in data and data["category_id"]:
                    category_query = select(Category).where(
                        and_(
                            Category.id == data["category_id"],
                            Category.is_deleted == False
                        )
                    )
                    category_result = await db.execute(category_query)
                    category = category_result.scalar_one_or_none()
                    
                    if not category:
                        logger.warning(f"更新版块失败: 分类不存在，ID={data['category_id']}")
                        return None
                
                # 更新版块字段
                for key, value in data.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
                
                section.updated_at = datetime.now()
                
                await db.commit()
                await db.refresh(section)
                
                # 转换为响应对象
                section_dict = {c.name: getattr(section, c.name) for c in section.__table__.columns}
                return SectionResponse(**section_dict)
            except Exception as e:
                await db.rollback()
                logger.error(f"更新版块失败: {str(e)}")
                return None

    async def delete_section(self, section_id: int) -> bool:
        """删除版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.async_get_db() as db:
            try:
                # 软删除版块
                stmt = (
                    update(Section)
                    .where(
                        and_(
                            Section.id == section_id,
                            Section.is_deleted == False
                        )
                    )
                    .values(
                        is_deleted=True,
                        deleted_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                )
                
                result = await db.execute(stmt)
                await db.commit()
                
                return result.rowcount > 0
            except Exception as e:
                await db.rollback()
                logger.error(f"删除版块失败: {str(e)}")
                return False

    async def get_section_stats(self) -> List[SectionStatsResponse]:
        """获取版块统计
        
        返回各个版块的帖子数量统计
        
        Returns:
            List[SectionStatsResponse]: 版块统计列表
        """
        async with self.async_get_db() as db:
            try:
                # 获取所有非删除版块
                sections_query = select(Section).where(Section.is_deleted == False)
                sections_result = await db.execute(sections_query)
                sections = sections_result.scalars().all()
                
                stats_list = []
                
                # 获取每个版块的帖子数量
                for section in sections:
                    posts_count_query = select(func.count()).select_from(Post).where(
                        and_(
                            Post.section_id == section.id,
                            Post.is_deleted == False
                        )
                    )
                    posts_count_result = await db.execute(posts_count_query)
                    posts_count = posts_count_result.scalar_one() or 0
                    
                    # 获取所属分类信息
                    category_name = None
                    if section.category_id:
                        category_query = select(Category.name).where(Category.id == section.category_id)
                        category_result = await db.execute(category_query)
                        category_name = category_result.scalar_one_or_none()
                    
                    # 构建统计对象
                    section_dict = {c.name: getattr(section, c.name) for c in section.__table__.columns}
                    section_dict["posts_count"] = posts_count
                    section_dict["category_name"] = category_name
                    
                    stats_list.append(SectionStatsResponse(**section_dict))
                
                # 按照帖子数量降序排序
                stats_list.sort(key=lambda x: x.posts_count, reverse=True)
                
                return stats_list
            except Exception as e:
                logger.error(f"获取版块统计失败: {str(e)}")
                return []

    # def model_to_dict(self, model) -> Dict[str, Any]:
    #     """将模型对象转换为字典
        
    #     Args:
    #         model: 模型对象
            
    #     Returns:
    #         Dict[str, Any]: 字典表示
    #     """
    #     result = {}
    #     for column in model.__table__.columns:
    #         result[column.name] = getattr(model, column.name)
    #     return result 