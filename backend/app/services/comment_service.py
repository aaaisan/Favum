from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from ..db.repositories.comment_repository import CommentRepository
from ..core.exceptions import BusinessException

logger = logging.getLogger(__name__)

class CommentService:
    """评论服务类
    
    提供评论相关的业务逻辑，包括评论的创建、查询、更新和删除等功能。
    """
    
    def __init__(self):
        """初始化评论服务"""
        self.comment_repository = CommentRepository()
    
    async def get_comment_detail(self, comment_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """获取评论详情
        
        Args:
            comment_id: 评论ID
            include_deleted: 是否包含已删除的评论
            
        Returns:
            Optional[Dict[str, Any]]: 评论信息，不存在则返回None
            
        Raises:
            BusinessException: 当评论不存在时抛出业务异常
        """
        comment = await self.comment_repository.get_by_id(comment_id, include_deleted)
        
        if not comment:
            raise BusinessException(
                status_code=404,
                error_code="COMMENT_NOT_FOUND",
                message="评论不存在"
            )
            
        return comment
    
    async def get_comments_by_post(
        self, 
        post_id: int, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取帖子下的评论列表
        
        Args:
            post_id: 帖子ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_deleted: 是否包含已删除的评论
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 评论列表和总数
        """
        return await self.comment_repository.get_comments_by_post(
            post_id=post_id,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted
        )
    
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新评论
        
        Args:
            comment_data: 评论数据
            
        Returns:
            Dict[str, Any]: 创建的评论
            
        Raises:
            BusinessException: 当参数无效或创建失败时抛出业务异常
        """
        # 验证必要字段
        required_fields = ["content", "author_id", "post_id"]
        for field in required_fields:
            if field not in comment_data:
                raise BusinessException(
                    status_code=400,
                    error_code="INVALID_DATA",
                    message=f"缺少必要字段: {field}"
                )
        
        # 内容不能为空
        if not comment_data.get("content", "").strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_CONTENT",
                message="评论内容不能为空"
            )
        
        # 创建评论
        try:
            comment = await self.comment_repository.create(comment_data)
            return comment
        except Exception as e:
            logger.error(f"创建评论失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="CREATE_FAILED",
                message="创建评论失败"
            )
    
    async def update_comment(self, comment_id: int, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新评论
        
        Args:
            comment_id: 评论ID
            user_id: 当前用户ID
            data: 更新的数据
            
        Returns:
            Dict[str, Any]: 更新后的评论
            
        Raises:
            BusinessException: 当评论不存在或无权限时抛出业务异常
        """
        # 验证内容不能为空
        if "content" in data and not data.get("content", "").strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_CONTENT",
                message="评论内容不能为空"
            )
        
        # 获取评论
        comment = await self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise BusinessException(
                status_code=404,
                error_code="COMMENT_NOT_FOUND",
                message="评论不存在"
            )
        
        # 检查权限（只有评论作者可以修改）
        if comment.get("author_id") != user_id:
            raise BusinessException(
                status_code=403,
                error_code="PERMISSION_DENIED",
                message="没有权限修改此评论"
            )
        
        # 更新评论
        updated_comment = await self.comment_repository.update(comment_id, data)
        if not updated_comment:
            raise BusinessException(
                status_code=404,
                error_code="UPDATE_FAILED",
                message="更新评论失败"
            )
            
        return updated_comment
    
    async def delete_comment(self, comment_id: int, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """删除评论
        
        Args:
            comment_id: 评论ID
            user_id: 当前用户ID
            is_admin: 是否为管理员
            
        Returns:
            Dict[str, Any]: 删除结果信息
            
        Raises:
            BusinessException: 当评论不存在或无权限时抛出业务异常
        """
        # 获取评论
        comment = await self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise BusinessException(
                status_code=404,
                error_code="COMMENT_NOT_FOUND",
                message="评论不存在"
            )
        
        # 检查权限（评论作者或管理员可以删除）
        if not is_admin and comment.get("author_id") != user_id:
            raise BusinessException(
                status_code=403,
                error_code="PERMISSION_DENIED",
                message="没有权限删除此评论"
            )
        
        # 软删除评论
        success = await self.comment_repository.soft_delete(comment_id)
        if not success:
            raise BusinessException(
                status_code=500,
                error_code="DELETE_FAILED",
                message="删除评论失败"
            )
            
        return {"message": "评论已删除", "id": comment_id}
    
    async def restore_comment(self, comment_id: int) -> Dict[str, Any]:
        """恢复已删除的评论
        
        Args:
            comment_id: 评论ID
            
        Returns:
            Dict[str, Any]: 恢复的评论
            
        Raises:
            BusinessException: 当评论不存在或未被删除时抛出业务异常
        """
        # 获取评论详情，包括已删除的
        comment = await self.comment_repository.get_by_id(comment_id, include_deleted=True)
        if not comment:
            raise BusinessException(
                status_code=404,
                error_code="COMMENT_NOT_FOUND",
                message="评论不存在"
            )
        
        # 检查评论是否已删除
        if not comment.get("is_deleted"):
            raise BusinessException(
                status_code=400,
                error_code="COMMENT_NOT_DELETED",
                message="评论未被删除"
            )
        
        # 恢复评论
        restored_comment = await self.comment_repository.restore(comment_id)
        if not restored_comment:
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_FAILED",
                message="恢复评论失败"
            )
            
        return restored_comment 