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
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy import asc, select
from sqlalchemy import desc, asc, select
import logging
from datetime import datetime

from ..core.base_service import BaseService
from ..db.models import Post, Tag, VoteType
from ..db.repositories.post_repository import PostRepository
from ..core.exceptions import BusinessException
from ..services.favorite_service import FavoriteService

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
        """
        return await self.repository.get_with_relations(post_id, include_hidden)
    
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
        return await self.repository.get_posts(
            skip=skip,
            limit=limit,
            include_hidden=include_hidden,
            category_id=category_id,
            section_id=section_id,
            author_id=author_id,
            tag_ids=tag_ids,
            sort_field=sort_field,
            sort_order=sort_order
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
        # 提取标签ID列表，不是Post模型的直接字段
        tag_ids = post_data.pop("tag_ids", []) if "tag_ids" in post_data else []
        
        # 创建帖子基本信息
        created_post = await self.create(post_data)
        
        # 如果有标签，创建标签关联
        if tag_ids:
            await self.repository.update_tags(created_post["id"], tag_ids)
            
            # 重新获取帖子信息，包含标签
            return await self.get_post_detail(created_post["id"])
            
        return created_post
    
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
        # 检查帖子是否存在
        post = await self.get(post_id)
        if not post:
            return None
            
        # 提取标签ID列表
        tag_ids = post_data.pop("tag_ids", None)
        
        # 更新帖子基本信息
        updated_post = await self.update(post_id, post_data)
        
        # 如果提供了标签ID，更新标签关联
        if tag_ids is not None:
            await self.repository.update_tags(post_id, tag_ids)
            
            # 重新获取帖子信息，包含标签
            return await self.get_post_detail(post_id)
            
        return updated_post
    
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
        # 先通过基础查询获取帖子（包括已删除的）
        query = await self.repository.execute_query(
            select(self.model).where(self.model.id == post_id)
        )
        post = query.first()
        
        if not post:
            raise BusinessException(
                status_code=404,
                error_code="POST_NOT_FOUND",
                message="帖子不存在"
            )
            
        # 如果帖子未被删除，抛出错误
        if not post.is_deleted:
            raise BusinessException(
                status_code=400,
                error_code="POST_NOT_DELETED",
                message="帖子未被删除，无需恢复"
            )
            
        # 执行恢复
        success = await self.repository.restore(post_id)
        if not success:
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_FAILED",
                message="恢复帖子失败"
            )
            
        # 获取并返回更新后的帖子信息
        return await self.get_post_detail(post_id)
    
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
        return await self.get_post_detail(post_id, include_hidden=True)
    
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
            
            return result
        except Exception as e:
            # 记录错误
            logging.error(f"投票失败: {str(e)}")
            
            # 如果是已知的业务异常，直接抛出
            if isinstance(e, BusinessException):
                raise e
            
            # 其他异常转换为业务异常
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
                logging.warning(f"更新收藏计数失败: {str(e)}")
            
            return {
                "post_id": post_id,
                "user_id": user_id,
                "status": "favorited",
                "success": result.get("success", True),
                "message": result.get("message", "收藏成功")
            }
        except Exception as e:
            # 记录错误
            logging.error(f"收藏帖子失败: {str(e)}")
            
            # 如果是已知的业务异常，直接抛出
            if isinstance(e, BusinessException):
                raise e
            
            # 其他异常转换为业务异常
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