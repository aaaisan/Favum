from typing import Dict, List, Optional, Any, Tuple
import logging

from ..db.repositories.category_repository import CategoryRepository
from ..core.exceptions import BusinessException
from ..schemas.inputs.category import CategorySchema
from ..schemas.responses.category import CategoryDetailResponse, CategoryDeleteResponse, CategoryListResponse

logger = logging.getLogger(__name__)

class CategoryService:
    """分类服务类
    
    提供分类相关的业务逻辑，包括分类的创建、查询、更新和删除等功能。
    """
    
    def __init__(self):
        """初始化分类服务"""
        self.category_repository = CategoryRepository()
    
    async def get_category_detail(self, category_id: int, include_deleted: bool = False) -> Optional[CategoryDetailResponse]:
        """获取分类详情
        
        Args:
            category_id: 分类ID
            include_deleted: 是否包含已删除的分类
            
        Returns:
            Optional[Dict[str, Any]]: 分类信息，不存在或已删除（且不包含已删除）则返回None
        """
        try:
            category = await self.category_repository.get_by_id(category_id, include_deleted)
            return category
        except Exception as e:
            logger.error(f"获取分类详情失败，分类ID: {category_id}, 错误: {str(e)}", exc_info=True)
            return None
    
    async def get_category_by_name(self, name: str) -> Optional[CategoryDetailResponse]:
        """根据名称获取分类
        
        Args:
            name: 分类名称
            
        Returns:
            Optional[Dict[str, Any]]: 分类信息，不存在则返回None
        """
        return await self.category_repository.get_by_name(name)
    
    async def get_categories(self, skip: int = 0, limit: int = 100) -> Tuple[List[CategorySchema], int]:
        """获取分类列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[CategoryBase], int]: 分类列表和总数
        """
        return await self.category_repository.get_all(skip, limit)
    
    async def create_category(self, category_data: CategorySchema) -> CategorySchema:
        """创建分类
        
        Args:
            category_data: 分类数据
            
        Returns:
            Dict[str, Any]: 创建的分类
            
        Raises:
            BusinessException: 当参数无效或创建失败时抛出业务异常
        """
        # 验证必要字段
        if "name" not in category_data or not category_data["name"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_NAME",
                message="分类名称不能为空"
            )
        
        # 创建分类
        try:
            category = await self.category_repository.create(category_data)
            return category
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"创建分类失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="CREATE_FAILED",
                message="创建分类失败"
            )
    
    async def update_category(self, category_id: int, data: CategorySchema) -> CategoryRepository:
        """更新分类
        
        Args:
            category_id: 分类ID
            data: 更新的数据
            
        Returns:
            Dict[str, Any]: 更新后的分类
            
        Raises:
            BusinessException: 当分类不存在或更新失败时抛出业务异常
        """
        # 验证数据
        if "name" in data and not data["name"].strip():
            raise BusinessException(
                status_code=400,
                error_code="INVALID_NAME",
                message="分类名称不能为空"
            )
        
        try:
            # 更新分类
            updated_category = await self.category_repository.update(category_id, data)
            if not updated_category:
                raise BusinessException(
                    status_code=404,
                    error_code="CATEGORY_NOT_FOUND",
                    message="分类不存在"
                )
                
            return updated_category
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"更新分类失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="UPDATE_FAILED",
                message="更新分类失败"
            )
    
    async def delete_category(self, category_id: int) -> CategoryDeleteResponse:
        """删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Dict[str, Any]: 删除结果信息
            
        Raises:
            BusinessException: 当分类不存在或删除失败时抛出业务异常
        """
        try:
            # 软删除分类
            success = await self.category_repository.soft_delete(category_id)
            if not success:
                raise BusinessException(
                    status_code=404,
                    error_code="CATEGORY_NOT_FOUND",
                    message="分类不存在"
                )
                
            return {"message": "分类已删除", "id": category_id}
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"删除分类失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="DELETE_FAILED",
                message="删除分类失败"
            )
    
    async def restore_category(self, category_id: int) -> CategoryDetailResponse:
        """恢复已删除的分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Dict[str, Any]: 恢复的分类
            
        Raises:
            BusinessException: 当分类不存在或未被删除时抛出业务异常
        """
        try:
            # 获取分类详情，包括已删除的
            category = await self.category_repository.get_by_id(category_id, include_deleted=True)
            if not category:
                raise BusinessException(
                    status_code=404,
                    error_code="CATEGORY_NOT_FOUND",
                    message="分类不存在"
                )
            
            # 检查分类是否已删除
            if not category.get("is_deleted"):
                raise BusinessException(
                    status_code=400,
                    error_code="CATEGORY_NOT_DELETED",
                    message="分类未被删除"
                )
            
            # 恢复分类
            restored_category = await self.category_repository.restore(category_id)
            if not restored_category:
                raise BusinessException(
                    status_code=500,
                    error_code="RESTORE_FAILED",
                    message="恢复分类失败"
                )
                
            return restored_category
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"恢复分类失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="RESTORE_FAILED",
                message="恢复分类失败"
            )
    
    async def reorder_categories(self, parent_id: Optional[int], category_ids: List[int]) -> CategoryListResponse:
        """重新排序分类
        
        Args:
            parent_id: 父分类ID，None表示顶级分类
            category_ids: 按新顺序排列的分类ID列表
            
        Returns:
            List[Dict[str, Any]]: 更新后的分类列表
            
        Raises:
            BusinessException: 当分类不存在或排序失败时抛出业务异常
        """
        try:
            # 验证参数
            if not category_ids:
                raise BusinessException(
                    status_code=400,
                    error_code="INVALID_CATEGORIES",
                    message="分类ID列表不能为空"
                )
            
            # 如果指定了父分类，验证父分类是否存在
            if parent_id is not None:
                parent = await self.category_repository.get_by_id(parent_id)
                if not parent:
                    raise BusinessException(
                        status_code=404,
                        error_code="PARENT_NOT_FOUND",
                        message="父分类不存在"
                    )
            
            # 重新排序分类
            return await self.category_repository.reorder(parent_id, category_ids)
        except BusinessException as e:
            # 直接抛出业务异常
            raise e
        except Exception as e:
            # 记录日志并抛出通用异常
            logger.error(f"重新排序分类失败: {str(e)}")
            raise BusinessException(
                status_code=500,
                error_code="REORDER_FAILED",
                message="重新排序分类失败"
            ) 