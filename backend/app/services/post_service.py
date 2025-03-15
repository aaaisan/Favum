"""
帖子服务

提供帖子相关的业务逻辑实现，包括：
- 帖子的创建、读取、更新和删除
- 帖子标签管理
- 帖子投票和评分
- 帖子可见性控制
- 帖子状态管理

该服务层依赖于PostRepository进行数据访问，提供更高层次的业务抽象。
"""

from typing import Dict, Any, List, Optional, Tuple
# from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy import asc, select
# from sqlalchemy import desc, asc, select
import logging
from datetime import datetime

from ..core.base_service import BaseService
from ..db.models import Post, Tag, VoteType
from ..db.repositories.post_repository import PostRepository
from ..core.exceptions import BusinessException, BusinessErrorCode
from ..services.favorite_service import FavoriteService

logger = logging.getLogger(__name__)

class PostService(BaseService):
    """帖子业务逻辑服务"""
    
    def __init__(self):
        """初始化帖子服务
        
        创建PostRepository实例，并传递给基类
        """
        self.repository = PostRepository()
        super().__init__(Post, self.repository)
    
    async def get_post_detail(self, post_id: int, include_hidden: bool = False) -> Optional[Dict[str, Any]]:
        """获取帖子详情
        
        包含分类、版块、标签等关联信息
        
        Args:
            post_id: 帖子ID
            include_hidden: 是否包含隐藏的帖子
            
        Returns:
            Optional[Dict[str, Any]]: 帖子详情，不存在则返回None
            
        Raises:
            BusinessException: 当获取帖子详情失败时抛出
        """
        try:
            logger.info(f"获取帖子详情，ID: {post_id}, include_hidden: {include_hidden}")
            post = await self.repository.get_with_relations(post_id, include_hidden)
            
            if not post:
                logger.warning(f"帖子不存在，ID: {post_id}")
                return None
                
            # 确保返回的帖子有一个标签列表
            if "tags" not in post:
                post["tags"] = []
                
            # 确保返回的帖子有一个评论列表
            if "comments" not in post:
                post["comments"] = []
            
            # 格式化日期时间字段
            self._format_datetime_fields(post)
            
            logger.info(f"成功获取帖子详情，ID: {post_id}")
            return post
        except Exception as e:
            logger.error(f"获取帖子详情失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="GET_POST_DETAIL_ERROR",
                message=f"获取帖子详情失败: {str(e)}"
            )
    
    def _format_datetime_fields(self, data: Dict[str, Any]) -> None:
        """格式化字典中的日期时间字段为字符串
        
        Args:
            data: 包含日期时间字段的字典
        """
        datetime_fields = ['created_at', 'updated_at', 'deleted_at', 'last_used_at']
        for field in datetime_fields:
            if field in data and data[field] and not isinstance(data[field], str):
                data[field] = data[field].isoformat()
        
        # 处理嵌套字段
        for key, value in data.items():
            if isinstance(value, dict):
                self._format_datetime_fields(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._format_datetime_fields(item)
    
    async def get_posts(
        self,
        skip: int = 0,
        limit: int = 10,
        include_hidden: bool = False,
        category_id: Optional[int] = None,
        section_id: Optional[int] = None,
        author_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "desc",
    ) -> Tuple[List[Dict], int]:
        """
        获取帖子列表
        """
        try:
            logger.info(f"PostService.get_posts: Starting with params: skip={skip}, limit={limit}")
            
            filter_options = {}
            if category_id is not None:
                filter_options["category_id"] = category_id
                
            if section_id is not None:
                filter_options["section_id"] = section_id
                
            if author_id is not None:
                filter_options["author_id"] = author_id
                
            if tag_ids:
                filter_options["tag_ids"] = tag_ids
                
            # 记录过滤条件
            logger.info(f"PostService.get_posts: Filter options: {filter_options}")
            logger.info(f"PostService.get_posts: Sort field: {sort_field}, sort order: {sort_order}")
            
            # 调用repository层获取帖子
            posts, total = await self.repository.get_posts(
                skip=skip,
                limit=limit,
                include_hidden=include_hidden,
                include_deleted=False,
                sort_field=sort_field,
                sort_order=sort_order,
                **filter_options
            )
            
            # 格式化日期字段
            result_posts = []
            for post in posts:
                # 确保我们有一个字典，如果post是数据库模型则转换为字典
                post_dict = self.model_to_dict(post)
                result_posts.append(post_dict)
                
            logger.info(f"PostService.get_posts: Successfully retrieved {len(result_posts)} posts")
            return result_posts, total
        except Exception as e:
            logger.error(f"PostService.get_posts: Error retrieving posts: {str(e)}")
            logger.exception("Exception traceback:")
            raise BusinessException(code=BusinessErrorCode.POST_NOT_FOUND, message=f"获取帖子列表失败: {str(e)}")
    
    async def create_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建帖子
        
        处理标签关联和验证
        
        Args:
            post_data: 帖子数据，包括标题、内容、分类等
            
        Returns:
            Dict[str, Any]: 创建成功的帖子
            
        Raises:
            BusinessException: 当必要字段缺失或验证失败时
        """
        try:
            logger.info(f"开始创建帖子: {post_data.get('title', '无标题')}")
            
            # 验证必要字段
            required_fields = ['title', 'content', 'author_id', 'section_id', 'category_id']
            for field in required_fields:
                if field not in post_data or not post_data[field]:
                    logger.error(f"创建帖子失败: 缺少必要字段 {field}")
                    raise BusinessException(
                        code=BusinessErrorCode.VALIDATION_ERROR,
                        message=f"缺少必要字段: {field}"
                    )
            
            # 额外验证
            if len(post_data.get('title', '')) < 3:
                raise BusinessException(
                    code=BusinessErrorCode.VALIDATION_ERROR,
                    message="标题长度至少为3个字符"
                )
            
            if len(post_data.get('content', '')) < 10:
                raise BusinessException(
                    code=BusinessErrorCode.VALIDATION_ERROR,
                    message="内容长度至少为10个字符"
                )
            
            # 检查外键约束 - 验证作者ID是否存在
            author_id = post_data.get('author_id')
            if author_id:
                from ..db.repositories.user_repository import UserRepository
                user_repo = UserRepository()
                user = await user_repo.get(author_id)
                if not user:
                    raise BusinessException(
                        code=BusinessErrorCode.VALIDATION_ERROR,
                        message=f"作者ID不存在: {author_id}"
                    )
            
            # 检查外键约束 - 验证分类ID是否存在
            category_id = post_data.get('category_id')
            if category_id:
                # 导入CategoryRepository可能需要根据你的项目结构调整
                from ..db.repositories.category_repository import CategoryRepository
                category_repo = CategoryRepository()
                category = await category_repo.get(category_id)
                if not category:
                    raise BusinessException(
                        code=BusinessErrorCode.VALIDATION_ERROR,
                        message=f"分类ID不存在: {category_id}"
                    )
            
            # 检查外键约束 - 验证版块ID是否存在
            section_id = post_data.get('section_id')
            if section_id:
                # 导入SectionRepository可能需要根据你的项目结构调整
                from ..db.repositories.section_repository import SectionRepository
                section_repo = SectionRepository()
                section = await section_repo.get(section_id)
                if not section:
                    raise BusinessException(
                        code=BusinessErrorCode.VALIDATION_ERROR,
                        message=f"版块ID不存在: {section_id}"
                    )
            
            # 确保有tag_ids字段，即使是空列表
            if 'tag_ids' not in post_data:
                post_data['tag_ids'] = []
            
            # 使用repository的create方法创建帖子
            # 该方法已被覆盖，能够处理标签关联
            logger.info(f"准备创建帖子: {post_data}")
            created_post = await self.repository.create(post_data)
            
            if not created_post:
                logger.error("创建帖子失败")
                raise BusinessException(
                    code=BusinessErrorCode.CREATE_ERROR,
                    message="创建帖子失败"
                )
            
            logger.info(f"成功创建帖子，ID: {created_post.get('id')}")
            return created_post
        except BusinessException:
            # 直接传递业务异常
            raise
        except Exception as e:
            logger.error(f"创建帖子失败: {str(e)}", exc_info=True)
            raise BusinessException(
                code=BusinessErrorCode.INTERNAL_ERROR,
                message=f"创建帖子时发生错误: {str(e)}"
            )
    
    async def update_post(self, post_id: int, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新帖子
        
        处理标签关联和基本信息更新
        
        Args:
            post_id: 帖子ID
            post_data: 更新的帖子数据
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的帖子，不存在则返回None
            
        Raises:
            BusinessException: 当帖子不存在或验证失败时
        """
        try:
            # 检查帖子是否存在
            post = await self.get(post_id)
            if not post:
                logger.warning(f"更新帖子失败: 帖子不存在，ID: {post_id}")
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 提取标签ID列表
            tag_ids = post_data.pop("tag_ids", None)
            
            # 更新帖子基本信息
            updated_post = await self.update(post_id, post_data)
            
            # 如果提供了标签ID，更新标签关联
            if tag_ids is not None:
                await self.repository.update_tags(post_id, tag_ids)
            
            # 重新获取帖子信息，包含标签
            updated_post = await self.get_post_detail(post_id)
        
            # 格式化日期时间字段
            if updated_post:
                self._format_datetime_fields(updated_post)
            
            return updated_post
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            logger.error(f"更新帖子失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="UPDATE_POST_ERROR",
                message=f"更新帖子失败: {str(e)}"
            )
    
    async def delete_post(self, post_id: int) -> bool:
        """软删除帖子
        
        将帖子标记为已删除，而不是物理删除
        
        Args:
            post_id: 帖子ID
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            BusinessException: 当帖子不存在时
        """
        # 检查帖子是否存在
        post = await self.get(post_id)
        if not post:
            raise BusinessException(
                status_code=404,
                error_code="POST_NOT_FOUND",
                message="帖子不存在"
            )
            
        # 如果帖子已经是删除状态，返回成功
        if post.get("is_deleted"):
            return True
            
        # 执行软删除
        return await self.repository.soft_delete(post_id)
    
    async def restore_post(self, post_id: int) -> Dict[str, Any]:
        """恢复已删除的帖子
        
        将标记为删除的帖子恢复为正常状态
        
        Args:
            post_id: 帖子ID
            
        Returns:
            Dict[str, Any]: 恢复后的帖子信息
            
        Raises:
            BusinessException: 当帖子不存在或未被删除时
        """
        try:
            # 先通过基础查询获取帖子（包括已删除的）
            query = await self.repository.execute_query(
                select(self.model).where(self.model.id == post_id)
            )
            post = query.first()
            
            if not post:
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 如果帖子未被删除，抛出错误
            if not post.is_deleted:
                raise BusinessException(
                    status_code=400,
                    code="POST_NOT_DELETED",
                    message="帖子未被删除，无需恢复"
                )
            
            # 执行恢复
            success = await self.repository.restore(post_id)
            if not success:
                raise BusinessException(
                    status_code=500,
                    code="RESTORE_FAILED",
                    message="恢复帖子失败"
                )
            
            # 获取并返回更新后的帖子信息
            restored_post = await self.get_post_detail(post_id)
            
            # 格式化日期时间字段
            if restored_post:
                self._format_datetime_fields(restored_post)
            
            return restored_post
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            logger.error(f"恢复帖子失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="RESTORE_POST_ERROR",
                message=f"恢复帖子失败: {str(e)}"
            )
    
    async def toggle_visibility(self, post_id: int, is_hidden: bool) -> Dict[str, Any]:
        """切换帖子可见性
        
        Args:
            post_id: 帖子ID
            is_hidden: 是否隐藏
            
        Returns:
            Dict[str, Any]: 更新后的帖子信息
            
        Raises:
            BusinessException: 当帖子不存在时
        """
        try:
            # 检查帖子是否存在
            post = await self.get(post_id)
            if not post:
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 如果当前状态已经是目标状态，直接返回
            if post.get("is_hidden") == is_hidden:
                self._format_datetime_fields(post)
                return post
            
            # 执行可见性切换
            success = await self.repository.toggle_visibility(post_id, is_hidden)
            if not success:
                raise BusinessException(
                    status_code=500,
                    code="TOGGLE_FAILED",
                    message="切换帖子可见性失败"
                )
            
            # 获取并返回更新后的帖子信息
            updated_post = await self.get_post_detail(post_id, include_hidden=True)
            
            # 格式化日期时间字段
            if updated_post:
                self._format_datetime_fields(updated_post)
            
            return updated_post
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            logger.error(f"切换帖子可见性失败，帖子ID: {post_id}, 错误: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="TOGGLE_VISIBILITY_ERROR",
                message=f"切换帖子可见性失败: {str(e)}"
            )
    
    async def vote_post(self, post_id: int, user_id: int, vote_type: VoteType) -> Dict[str, Any]:
        """为帖子投票
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            vote_type: 投票类型，VoteType枚举
            
        Returns:
            Dict[str, Any]: 投票结果，包含投票计数和用户的投票状态
            
        Raises:
            BusinessException: 当帖子不存在或投票操作失败时
        """
        try:
            # 首先验证帖子是否存在
            post = await self.get_post_detail(post_id)
            if not post:
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 执行投票操作
            result = await self.repository.vote_post(post_id, user_id, vote_type)
            if result is None:
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 格式化结果中可能包含的日期时间字段
            self._format_datetime_fields(result)
            
            return result
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            # 记录错误
            logger.error(f"投票失败: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="VOTE_FAILED",
                message=f"投票失败: {str(e)}"
            )
    
    async def get_user_vote(self, post_id: int, user_id: int) -> Optional[str]:
        """获取用户对帖子的投票状态
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Optional[str]: 投票类型，'upvote'、'downvote'或None
        """
        return await self.repository.get_user_vote(post_id, user_id)
    
    async def get_vote_count(self, post_id: int) -> int:
        """获取帖子的投票数量
        
        Args:
            post_id: 帖子ID
            
        Returns:
            int: 帖子的净投票数（点赞数减去踩数）
            
        Raises:
            BusinessException: 当帖子不存在时抛出
        """
        # 检查帖子是否存在
        post = await self.repository.get(post_id)
        if not post:
            raise BusinessException(
                message="帖子不存在",
                code="POST_NOT_FOUND", 
                status_code=404
            )
              
        return await self.repository.get_vote_count(post_id)
    
    async def favorite_post(self, post_id: int, user_id: int) -> Dict[str, Any]:
        """收藏帖子
        
        Args:
            post_id: 帖子ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 包含收藏操作结果的字典
            
        Raises:
            BusinessException: 当帖子不存在或操作失败时
        """
        try:
            # 首先验证帖子是否存在
            post = await self.get_post_detail(post_id)
            if not post:
                raise BusinessException(
                    status_code=404,
                    code="POST_NOT_FOUND",
                    message="帖子不存在"
                )
            
            # 使用FavoriteService处理收藏逻辑
            favorite_service = FavoriteService()
            result = await favorite_service.add_favorite(post_id, user_id)
            
            # 更新帖子的收藏计数
            try:
                current_count = post.get("favorites_count", 0)
                await self.repository.update(post_id, {"favorites_count": current_count + 1})
            except Exception as e:
                logger.warning(f"更新收藏计数失败: {str(e)}")
            
            # 构建结果
            favorite_result = {
                "post_id": post_id,
                "user_id": user_id,
                "status": "favorited",
                "success": result.get("success", True),
                "message": result.get("message", "收藏成功")
            }
            
            # 格式化结果中可能包含的日期时间字段
            self._format_datetime_fields(favorite_result)
            
            return favorite_result
        except BusinessException:
            # 继续抛出业务异常
            raise
        except Exception as e:
            # 记录错误
            logger.error(f"收藏帖子失败: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="FAVORITE_FAILED",
                message=f"收藏帖子失败: {str(e)}"
            )

    def model_to_dict(self, model_instance):
        """
        将模型实例转换为字典
        
        参数:
        - model_instance: SQLAlchemy模型实例或已有字典
        
        返回:
        - 字典表示
        """
        try:
            # 如果已经是字典，直接返回
            if isinstance(model_instance, dict):
                return model_instance
            
            # 如果是None，返回None
            if model_instance is None:
                return None
            
            # 如果模型有to_dict方法，使用此方法
            if hasattr(model_instance, "to_dict") and callable(getattr(model_instance, "to_dict")):
                return model_instance.to_dict()
            
            # 否则，尝试构建字典表示
            result = {}
            # 如果是SQLAlchemy模型，获取所有列
            if hasattr(model_instance, "__table__"):
                for column in model_instance.__table__.columns:
                    column_name = column.name
                    value = getattr(model_instance, column_name)
                    # 转换datetime为ISO格式字符串
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    result[column_name] = value
            else:
                # 回退方案：尝试获取对象的__dict__
                for key, value in model_instance.__dict__.items():
                    if not key.startswith('_'):  # 排除私有属性
                        # 转换datetime为ISO格式字符串
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"PostService.model_to_dict: Error converting model to dict: {str(e)}")
            # 返回空字典而不是抛出异常，以避免中断处理流程
            return {}

def get_post_service() -> PostService:
    """创建PostService实例的依赖函数
    
    用于FastAPI依赖注入系统
    
    Returns:
        PostService: 帖子服务实例
    """
    return PostService() 