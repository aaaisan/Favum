from typing import Dict, List, Any, Tuple
from typing import Dict, List, Optional, Any, Tuple
import logging

from ..db.repositories.section_repository import SectionRepository
from ..core.exceptions import BusinessException

logger = logging.getLogger(__name__)

class SectionService:
    """版块服务类
    
    提供版块相关的业务逻辑，包括版块的创建、查询、更新和删除，以及版主管理等功能。
    """
    
    def __init__(self):
        """初始化版块服务"""
        self.section_repository = SectionRepository()
    
    async def get_section_detail(self, section_id: int, include_deleted: bool = False) -> Dict[str, Any]:
        """获取版块详情
        
        Args:
            section_id: 版块ID
            include_deleted: 是否包含已删除的版块
            
        Returns:
            Dict[str, Any]: 版块信息
            
        Raises:
            BusinessException: 当版块不存在时抛出业务异常
        """
        section = await self.section_repository.get_by_id(section_id, include_deleted)
        
        if not section:
            raise BusinessException(
                status_code=404,
                error_code="SECTION_NOT_FOUND",
                message="版块不存在"
            )
            
        return section
    
    async def get_sections(self, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取版块列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 版块列表和总数
        """
        return await self.section_repository.get_all(skip, limit)
    
    async def create_section(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建版块
        
        Args:
            section_data: 版块数据
            
        Returns:
            Dict[str, Any]: 创建的版块
            
        Raises:
            BusinessException: 当参数无效或创建失败时抛出业务异常
        """
        # 验证必要字段
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in section_data or not str(section_data[field]).strip():
                raise BusinessException(
                    status_code=400,
                    error_code="INVALID_DATA",
                    message=f"缺少必要字段或字段为空: {field}"
                )
        
        # 创建版块
        try:
            section = await self.section_repository.create(section_data)
            return section
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"创建版块失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="CREATE_FAILED",
                message="创建版块失败"
            )
    
    async def update_section(self, section_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新版块
        
        Args:
            section_id: 版块ID
            data: 更新的数据
            
        Returns:
            Dict[str, Any]: 更新后的版块
            
        Raises:
            BusinessException: 当版块不存在或更新失败时抛出业务异常
        """
        # 验证数据
        if "name" in data and not data["name"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_NAME",
                message="版块名称不能为空"
            )
        
        if "description" in data and not data["description"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_DESCRIPTION",
                message="版块描述不能为空"
            )
        
        try:
            # 更新版块
            updated_section = await self.section_repository.update(section_id, data)
            if not updated_section:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
                
            return updated_section
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"更新版块失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="UPDATE_FAILED",
                message="更新版块失败"
            )
    
    async def delete_section(self, section_id: int) -> Dict[str, Any]:
        """删除版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            Dict[str, Any]: 删除结果信息
            
        Raises:
            BusinessException: 当版块不存在或删除失败时抛出业务异常
        """
        try:
            # 软删除版块
            success = await self.section_repository.soft_delete(section_id)
            if not success:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
                
            return {"message": "版块已删除", "id": section_id}
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"删除版块失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="DELETE_FAILED",
                message="删除版块失败"
            )
    
    async def restore_section(self, section_id: int) -> Dict[str, Any]:
        """恢复已删除的版块
        
        Args:
            section_id: 版块ID
            
        Returns:
            Dict[str, Any]: 恢复的版块
            
        Raises:
            BusinessException: 当版块不存在或未被删除时抛出业务异常
        """
        try:
            # 恢复版块
            restored_section = await self.section_repository.restore(section_id)
            if not restored_section:
                raise BusinessException(
                    status_code=404,
                    error_code="SECTION_NOT_FOUND",
                    message="版块不存在"
                )
                
            return restored_section
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"恢复版块失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_FAILED",
                message="恢复版块失败"
            )
    
    async def add_moderator(self, section_id: int, user_id: int) -> Dict[str, Any]:
        """添加版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            BusinessException: 当版块或用户不存在时抛出业务异常
        """
        try:
            # 添加版主
            success = await self.section_repository.add_moderator(section_id, user_id)
            if success:
                return {"message": "版主添加成功", "section_id": section_id, "user_id": user_id}
            else:
                raise BusinessException(
                    status_code=500,
                    error_code="ADD_MODERATOR_FAILED",
                    message="添加版主失败"
                )
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"添加版主失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="ADD_MODERATOR_FAILED",
                message="添加版主失败"
            )
    
    async def remove_moderator(self, section_id: int, user_id: int) -> Dict[str, Any]:
        """移除版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            BusinessException: 当版块不存在或用户不是版主时抛出业务异常
        """
        try:
            # 移除版主
            success = await self.section_repository.remove_moderator(section_id, user_id)
            if success:
                return {"message": "版主已移除", "section_id": section_id, "user_id": user_id}
            else:
                raise BusinessException(
                    status_code=500,
                    error_code="REMOVE_MODERATOR_FAILED",
                    message="移除版主失败"
                )
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"移除版主失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="REMOVE_MODERATOR_FAILED",
                message="移除版主失败"
            )
    
    async def restore_moderator(self, section_id: int, user_id: int) -> Dict[str, Any]:
        """恢复版主
        
        Args:
            section_id: 版块ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            BusinessException: 当版块不存在或记录不存在时抛出业务异常
        """
        try:
            # 恢复版主
            success = await self.section_repository.restore_moderator(section_id, user_id)
            if success:
                return {"message": "版主已恢复", "section_id": section_id, "user_id": user_id}
            else:
                raise BusinessException(
                    status_code=500,
                    error_code="RESTORE_MODERATOR_FAILED",
                    message="恢复版主失败"
                )
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"恢复版主失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_MODERATOR_FAILED",
                message="恢复版主失败"
            )
    
    async def get_section_posts(self, section_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取版块下的帖子
        
        Args:
            section_id: 版块ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 帖子列表和总数
            
        Raises:
            BusinessException: 当版块不存在时抛出业务异常
        """
        try:
            # 获取版块下的帖子
            return await self.section_repository.get_section_posts(section_id, skip, limit)
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"获取版块帖子失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="GET_POSTS_FAILED",
                message="获取版块帖子失败"
            )
    
    async def get_section_moderators(self, section_id: int) -> List[Dict[str, Any]]:
        """获取版块的版主列表
        
        Args:
            section_id: 版块ID
            
        Returns:
            List[Dict[str, Any]]: 版主用户列表
            
        Raises:
            BusinessException: 当版块不存在时抛出业务异常
        """
        try:
            # 获取版主列表
            moderators = await self.section_repository.get_moderators(section_id)
            return moderators
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"获取版主列表失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="GET_MODERATORS_FAILED",
                message="获取版主列表失败"
            ) 