from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc
from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import relationship

from ..models.section import Section
from ..models.user import User
from ..models.section_moderator import SectionModerator
from ..models.post import Post
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException

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
        async with self.session() as session:
            # 查询版块，不包括已删除的
            query = (
                select(Section)
                .where(Section.is_deleted == False)
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            sections = result.scalars().all()
            
            # 查询总数
            count_query = select(func.count(Section.id)).where(Section.is_deleted == False)
            count_result = await session.execute(count_query)
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
        async with self.session() as session:
            # 检查版块名称是否已存在
            name_query = select(Section).where(
                Section.name == section_data["name"],
                Section.is_deleted == False
            )
            name_result = await session.execute(name_query)
            existing = name_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="SECTION_EXISTS",
                    message="版块名称已存在"
                )
            
            # 创建版块
            section = Section(**section_data)
            session.add(section)
            await session.commit()
            await session.refresh(section)
            
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
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
            if not section or section.is_deleted:
                return None
            
            # 如果更新名称，检查是否重复
            if "name" in data and data["name"] != section.name:
                name_query = select(Section).where(
                    Section.name == data["name"],
                    Section.is_deleted == False
                )
                name_result = await session.execute(name_query)
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
            
            await session.commit()
            await session.refresh(section)
            
            # 返回更新后的版块
            return self.model_to_dict(section)
    
    async def soft_delete(self, section_id: int) -> bool:
        """软删除版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.session() as session:
            # 查询版块
            section = await session.get(Section, section_id)
            if not section or section.is_deleted:
                return False
                
            # 检查是否有关联的未删除帖子
            posts_query = select(func.count(Post.id)).where(
                Post.section_id == section_id,
                Post.is_deleted == False
            )
            posts_result = await session.execute(posts_query)
            post_count = posts_result.scalar() or 0
            
            if post_count > 0:
                # 有关联帖子，可以继续删除版块，但要记录警告日志
                # 这里不阻止删除，因为帖子仍然可以访问，只是不会显示在版块页面
                pass
            
            # 软删除版块
            section.is_deleted = True
            if hasattr(section, "deleted_at"):
                section.deleted_at = datetime.now()
            
            await session.commit()
            return True
    
    async def restore(self, section_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的版块，如果版块不存在或未被删除则返回None
        """
        async with self.session() as session:
            # 查询版块
            section = await session.get(Section, section_id)
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
            
            await session.commit()
            await session.refresh(section)
            
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
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
            
            # 检查用户是否存在
            user = await session.get(User, user_id)
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
            moderator_result = await session.execute(moderator_query)
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
            deleted_result = await session.execute(deleted_query)
            deleted_record = deleted_result.scalar_one_or_none()
            
            if deleted_record:
                # 恢复已删除的记录
                deleted_record.is_deleted = False
            else:
                # 创建新记录
                moderator = SectionModerator(section_id=section_id, user_id=user_id)
                session.add(moderator)
            
            # 更新用户角色为版主（如果不是管理员）
            if user.role not in ["admin", "super_admin", "moderator"]:
                user.role = "moderator"
            
            await session.commit()
            return True
    
    async def remove_moderator(self, section_id: int, user_id: int) -> bool:
        """移除版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
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
            moderator_result = await session.execute(moderator_query)
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
            other_sections_result = await session.execute(other_sections_query)
            other_sections_count = other_sections_result.scalar() or 0
            
            # 如果不是其他版块的版主，且不是管理员，则更新角色为普通用户
            if other_sections_count == 0:
                user = await session.get(User, user_id)
                if user and user.role == "moderator":
                    user.role = "user"
            
            await session.commit()
            return True
    
    async def restore_moderator(self, section_id: int, user_id: int) -> bool:
        """恢复版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
            if not section or section.is_deleted:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
            
            # 检查用户是否存在
            user = await session.get(User, user_id)
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
            moderator_result = await session.execute(moderator_query)
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
            
            await session.commit()
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
        
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
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
            posts_result = await session.execute(posts_query)
            posts = posts_result.unique().scalars().all()
            
            # 查询总数
            count_query = select(func.count(Post.id)).where(
                Post.section_id == section_id,
                Post.is_deleted == False
            )
            count_result = await session.execute(count_query)
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
        async with self.session() as session:
            # 检查版块是否存在
            section = await session.get(Section, section_id)
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
            
            result = await session.execute(query)
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