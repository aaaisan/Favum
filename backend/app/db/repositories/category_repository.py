from sqlalchemy import select, func, delete, text, insert, and_, or_, desc, asc
# from sqlalchemy import select, func, update, delete, text, insert, and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import logging

from ..models.category import Category
from .base_repository import BaseRepository
from ...core.exceptions import BusinessException, SQLAlchemyError

logger = logging.getLogger(__name__)

class CategoryRepository(BaseRepository):
    """分类仓库
    
    提供分类相关的数据库访问方法，包括查询、创建、更新和删除分类。
    """
    
    def __init__(self):
        """初始化分类仓库"""
        super().__init__(Category)
    
    async def get_by_id(self, category_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """根据ID获取分类
        
        Args:
            category_id: 分类ID
            include_deleted: 是否包含已删除的分类
            
        Returns:
            Optional[Dict[str, Any]]: 分类信息字典，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = select(Category).where(Category.id == category_id)
            
            if not include_deleted:
                query = query.where(Category.is_deleted == False)
                
            result = await db.execute(query)
            category = result.scalar_one_or_none()
            
            if category is None:
                return None
                
            # 获取子分类
            children_query = select(Category).where(
                Category.parent_id == category_id,
                Category.is_deleted == False
            ).order_by(Category.order)
            
            children_result = await db.execute(children_query)
            children = children_result.scalars().all()
            
            # 转换为字典并添加子分类
            category_dict = self.model_to_dict(category)
            category_dict["children"] = [self.model_to_dict(child) for child in children]
            
            return category_dict
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取分类
        
        Args:
            name: 分类名称
            
        Returns:
            Optional[Dict[str, Any]]: 分类信息字典，不存在则返回None
        """
        async with self.async_get_db() as db:
            query = select(Category).where(
                Category.name == name,
                Category.is_deleted == False
            )
            
            result = await db.execute(query)
            category = result.scalar_one_or_none()
            
            if category is None:
                return None
                
            return self.model_to_dict(category)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """获取所有顶级分类及其子分类
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 分类列表和总数
        """
        async with self.async_get_db() as db:
            try:
                # 查询顶级分类
                query = (
                    select(Category)
                    .where(
                        Category.parent_id.is_(None),
                        Category.is_deleted == False
                    )
                    .order_by(Category.order)
                    .offset(skip)
                    .limit(limit)
                )
            
                result = await db.execute(query)
                categories = result.scalars().all()
                
                # 查询总记录数
                count_query = (
                    select(func.count(Category.id))
                    .where(
                        Category.parent_id.is_(None),
                        Category.is_deleted == False
                    )
                )
                count_result = await db.execute(count_query)
                total = count_result.scalar_one()
                
            # 获取每个分类的子分类
                categories_data = []
                for category in categories:
                    category_dict = category.to_dict() if hasattr(category, 'to_dict') else {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "order": category.order,
                        "created_at": category.created_at,
                        "updated_at": category.updated_at if hasattr(category, 'updated_at') else None,
                        "is_deleted": category.is_deleted,
                        "parent_id": category.parent_id
                    }
                
                # 查询子分类
                    children_query = (
                        select(Category)
                        .where(
                            Category.parent_id == category.id,
                            Category.is_deleted == False
                        )
                        .order_by(Category.order)
                    )
                    children_result = await db.execute(children_query)
                    children = children_result.scalars().all()
                    
                    # 将子分类添加到父分类中
                    category_dict["children"] = []
                    for child in children:
                        child_dict = self.model_to_dict(child)
                        category_dict["children"].append(child_dict)
                    
                    categories_data.append(category_dict)
                
                return categories_data, total
            except SQLAlchemyError as e:
                raise e
    
    async def create(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建分类
        
        Args:
            category_data: 分类数据
            
        Returns:
            Dict[str, Any]: 创建的分类
        """
        async with self.async_get_db() as db:
            # 检查父分类是否存在
            if category_data.get("parent_id"):
                parent_query = select(Category).where(
                    Category.id == category_data["parent_id"],
                    Category.is_deleted == False
                )
                parent_result = await db.execute(parent_query)
                parent = parent_result.scalar_one_or_none()
                
                if parent is None:
                    raise BusinessException(
                        status_code=404,
                        error_code="PARENT_NOT_FOUND",
                        message="父分类不存在"
                    )
            
            # 检查分类名称是否已存在
            name_query = select(Category).where(
                Category.name == category_data["name"],
                Category.is_deleted == False
            )
            name_result = await db.execute(name_query)
            existing = name_result.scalar_one_or_none()
            
            if existing is not None:
                raise BusinessException(
                    status_code=400,
                    error_code="CATEGORY_EXISTS",
                    message="分类名称已存在"
                )
            
            # 如果没有指定order，则设置为当前同级最大order + 1
            if "order" not in category_data or category_data["order"] is None:
                order_query = select(func.max(Category.order)).where(
                    Category.parent_id == category_data.get("parent_id")
                )
                order_result = await db.execute(order_query)
                max_order = order_result.scalar() or -1
                category_data["order"] = max_order + 1
            
            # 创建分类
            category = Category(**category_data)
            db.add(category)
            await db.commit()
            await db.refresh(category)
            
            # 返回创建的分类
            category_dict = self.model_to_dict(category)
            category_dict["children"] = []
            
            return category_dict
    
    async def update(self, category_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新分类
        
        Args:
            category_id: 分类ID
            data: 要更新的数据
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的分类，不存在则返回None
        """
        async with self.async_get_db() as db:
            # 检查分类是否存在
            category = await db.get(Category, category_id)
            if not category or category.is_deleted:
                return None
            
            # 检查父分类是否存在
            if "parent_id" in data and data["parent_id"] is not None:
                # 如果父分类ID等于当前分类ID，不允许设置
                if data["parent_id"] == category_id:
                    raise BusinessException(
                        status_code=400,
                        error_code="INVALID_PARENT",
                        message="不能将分类设置为自己的子分类"
                    )
                
                parent_query = select(Category).where(
                    Category.id == data["parent_id"],
                    Category.is_deleted == False
                )
                parent_result = await db.execute(parent_query)
                parent = parent_result.scalar_one_or_none()
                
                if parent is None:
                    raise BusinessException(
                        status_code=404,
                        error_code="PARENT_NOT_FOUND",
                        message="父分类不存在"
                    )
                
                # 检查是否会形成循环引用
                # TODO: 实现更完整的循环检测
            
            # 如果更新名称，检查是否重复
            if "name" in data and data["name"] != category.name:
                name_query = select(Category).where(
                    Category.name == data["name"],
                    Category.is_deleted == False
                )
                name_result = await db.execute(name_query)
                existing = name_result.scalar_one_or_none()
                
                if existing is not None:
                    raise BusinessException(
                        status_code=400,
                        error_code="CATEGORY_EXISTS",
                        message="分类名称已存在"
                    )
            
            # 更新分类
            for key, value in data.items():
                if hasattr(category, key) and key != "id":
                    setattr(category, key, value)
            
            await db.commit()
            await db.refresh(category)
            
            # 获取子分类
            children_query = select(Category).where(
                Category.parent_id == category_id,
                Category.is_deleted == False
            ).order_by(Category.order)
            
            children_result = await db.execute(children_query)
            children = children_result.scalars().all()
            
            # 返回更新后的分类
            category_dict = self.model_to_dict(category)
            category_dict["children"] = [self.model_to_dict(child) for child in children]
            
            return category_dict
    
    async def soft_delete(self, category_id: int) -> bool:
        """软删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            async with self.async_get_db() as db:
                # 查询分类
                category = await db.get(Category, category_id)
                if not category or category.is_deleted:
                    return False
                
                # 检查是否有子分类
                children_query = select(func.count(Category.id)).where(
                    Category.parent_id == category_id,
                    Category.is_deleted == False
                )
                children_result = await db.execute(children_query)
                children_count = children_result.scalar() or 0
                
                if children_count > 0:
                    raise BusinessException(
                        status_code=400,
                        error_code="HAS_CHILDREN",
                        message="不能删除有子分类的分类"
                    )
                
                # 检查是否有关联的帖子 - 简化查询
                from ..models.post import Post
                posts_query = select(func.count(Post.id)).where(
                    Post.category_id == category_id,
                    Post.is_deleted == False
                )
                posts_result = await db.execute(posts_query)
                posts_count = posts_result.scalar() or 0
                
                if posts_count > 0:
                    raise BusinessException(
                        status_code=400,
                        error_code="HAS_POSTS",
                        message="不能删除有帖子的分类"
                    )
                
                # 软删除分类
                category.is_deleted = True
                category.deleted_at = datetime.now()
                
                await db.commit()
                return True
        except BusinessException:
            # 重新抛出业务异常
            raise
        except Exception as e:
            logger.error(f"软删除分类失败，分类ID: {category_id}, 错误: {str(e)}", exc_info=True)
            return False
    
    async def restore(self, category_id: int) -> Optional[Dict[str, Any]]:
        """恢复已删除的分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复后的分类，如果分类不存在或未被删除则返回None
        """
        async with self.async_get_db() as db:
            # 查询分类
            category = await db.get(Category, category_id)
            if not category:
                return None
            
            # 如果分类未被删除，则无需恢复
            if not category.is_deleted:
                return None
            
            # 如果有父分类，检查父分类是否已被删除
            if category.parent_id:
                parent = await db.get(Category, category.parent_id)
                if parent and parent.is_deleted:
                    raise BusinessException(
                        status_code=400,
                        error_code="PARENT_DELETED",
                        message="父分类已被删除，请先恢复父分类"
                    )
            
            # 恢复分类
            category.is_deleted = False
            category.deleted_at = None
            
            await db.commit()
            await db.refresh(category)
            
            # 获取子分类
            children_query = select(Category).where(
                Category.parent_id == category_id,
                Category.is_deleted == False
            ).order_by(Category.order)
            
            children_result = await db.execute(children_query)
            children = children_result.scalars().all()
            
            # 返回恢复后的分类
            category_dict = self.model_to_dict(category)
            category_dict["children"] = [self.model_to_dict(child) for child in children]
            
            return category_dict
    
    async def reorder(self, parent_id: Optional[int], category_ids: List[int]) -> List[Dict[str, Any]]:
        """重新排序分类
        
        Args:
            parent_id: 父分类ID，None表示顶级分类
            category_ids: 按新顺序排列的分类ID列表
            
        Returns:
            List[Dict[str, Any]]: 更新后的分类列表
        """
        async with self.async_get_db() as db:
            # 查询所有要排序的分类
            query = select(Category).where(
                Category.id.in_(category_ids),
                Category.parent_id == parent_id,
                Category.is_deleted == False
            )
            result = await db.execute(query)
            categories = result.scalars().all()
            
            # 检查是否所有分类都存在
            if len(categories) != len(category_ids):
                raise BusinessException(
                    status_code=400,
                    error_code="CATEGORIES_NOT_FOUND",
                    message="部分分类不存在或不属于同一父分类"
                )
            
            # 更新排序
            category_map = {category.id: category for category in categories}
            for index, category_id in enumerate(category_ids):
                category_map[category_id].order = index
            
            await db.commit()
            
            # 获取更新后的分类
            updated_categories = []
            for category_id in category_ids:
                category = category_map[category_id]
                updated_categories.append(self.model_to_dict(category))
            
            return updated_categories

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