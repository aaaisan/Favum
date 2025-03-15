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
# from datetime import datetime

from ..core.base_service import BaseService
from ..db.models import Post, Tag, VoteType
from ..db.repositories.post_repository import PostRepository
from ..core.exceptions import BusinessException
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
            
        Raises:
            BusinessException: 当获取帖子列表失败时抛出
        """
        try:
            logger.info(f"开始获取帖子列表: skip={skip}, limit={limit}, include_hidden={include_hidden}")
            logger.info(f"过滤条件: category_id={category_id}, section_id={section_id}, author_id={author_id}, tag_ids={tag_ids}")
            logger.info(f"排序: sort_field={sort_field}, sort_order={sort_order}")
            
            # 构建filter_options字典，包含所有过滤条件
            filter_options = {}
            
            # 添加过滤条件
            if include_hidden is not None:
                filter_options["include_hidden"] = include_hidden
                
            if category_id is not None:
                filter_options["category_id"] = category_id
                
            if section_id is not None:
                filter_options["section_id"] = section_id
                
            if author_id is not None:
                filter_options["author_id"] = author_id
                
            if tag_ids is not None:
                filter_options["tag_ids"] = tag_ids
            
            logger.info(f"构建的filter_options: {filter_options}")
            
            # 调用仓储层方法，正确传递参数
            posts, total = await self.repository.get_posts(
                skip=skip,
                limit=limit,
                filter_options=filter_options,
                sort_by=sort_field if sort_field else "created_at",
                sort_order=sort_order
            )
            
            # 格式化所有帖子的日期时间字段
            for post in posts:
                self._format_datetime_fields(post)
            
            return posts, total
        except Exception as e:
            logger.error(f"获取帖子列表失败: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="GET_POSTS_ERROR",
                message=f"获取帖子列表失败: {str(e)}"
            )
    
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
            required_fields = ['title', 'content', 'author_id']
            for field in required_fields:
                if field not in post_data or not post_data[field]:
                    logger.error(f"创建帖子失败: 缺少必要字段 {field}")
                    raise BusinessException(
                        status_code=400,
                        code="MISSING_REQUIRED_FIELD",
                        message=f"缺少必要字段: {field}"
                    )
            
            # 使用repository的create方法创建帖子
            # 该方法已被覆盖，能够处理标签关联
            logger.info(f"准备创建帖子: {post_data}")
            created_post = await super().create(post_data)
            
            if not created_post:
                logger.error("创建帖子失败")
                raise BusinessException(
                    status_code=500,
                    code="CREATE_POST_FAILED",
                    message="创建帖子失败"
                )
            
            logger.info(f"成功创建帖子，ID: {created_post.get('id')}")
            return created_post
        except BusinessException as be:
            # 直接传递业务异常
            logger.error(f"创建帖子时遇到业务异常: {be.message}")
            raise
        except Exception as e:
            logger.error(f"创建帖子失败: {str(e)}", exc_info=True)
            raise BusinessException(
                status_code=500,
                code="CREATE_POST_ERROR",
                message="创建帖子时发生错误"
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

def get_post_service() -> PostService:
    """创建PostService实例的依赖函数
    
    用于FastAPI依赖注入系统
    
    Returns:
        PostService: 帖子服务实例
    """
    return PostService() 