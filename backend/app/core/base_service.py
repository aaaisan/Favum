"""
基础服务模块

提供通用的服务层基类，实现常见的CRUD操作和错误处理。
设计目标：
- 减少重复代码
- 统一错误处理
- 标准化日志记录
- 类型安全的数据操作

主要功能：
- 创建记录
- 读取记录
- 更新记录
- 删除记录
- 列表查询
- 记录计数

所有操作都支持异步处理，并包含完整的错误处理和日志记录。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, TypeVar, Callable, TypeVar, Awaitable
# from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable, TypeVar, Awaitable
from fastapi import HTTPException

from .logging import get_logger
# 使用推迟的导入方式

logger = get_logger(__name__)

# 定义用于类型注解的泛型类型变量
T = TypeVar('T')

class BaseService:
    """
    基础服务类
    
    为所有服务类提供基础的CRUD操作实现。
    通过组合模式集成数据库仓储层，提供统一的服务接口。
    
    特性：
    - 异步操作支持
    - 统一的错误处理
    - 自动日志记录
    - 类型安全
    
    Attributes:
        model: SQLAlchemy模型类
        repository: 数据库仓储实例
        logger: 日志记录器实例
    """
    
    def __init__(
        self,
        model: Any,
        repository: Any
    ):
        """
        初始化服务实例
        
        Args:
            model: SQLAlchemy模型类，用于类型提示和验证
            repository: 数据库仓储类，处理实际的数据库操作
            
        Notes:
            - 自动创建仓储实例
            - 配置类专用的日志记录器
        """
        self.model = model
        self.repository = repository
        self.logger = get_logger(self.__class__.__name__)
    
    async def _handle_operation_error(
        self, 
        operation: Callable[..., Awaitable[T]],
        operation_name: str,
        error_message: str,
        error_status: int = 500,
        *args, 
        **kwargs
    ) -> T:
        """
        通用错误处理函数
        
        处理服务操作中的异常，提供统一的错误记录和异常转换。
        
        Args:
            operation: 要执行的异步操作函数
            operation_name: 操作名称，用于错误日志
            error_message: 错误消息，用于HTTP异常
            error_status: HTTP状态码，默认为500
            *args: 传递给操作函数的位置参数
            **kwargs: 传递给操作函数的关键字参数
            
        Returns:
            操作函数的返回值
            
        Raises:
            HTTPException: 当操作失败时抛出，状态码由error_status参数指定
        """
        try:
            result = await operation(*args, **kwargs)
            # 处理可能的404情况
            if result is None and error_status == 404:
                raise HTTPException(
                    status_code=404,
                    detail=error_message
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"{operation_name}失败: {str(e)}")
            raise HTTPException(
                status_code=error_status,
                detail=error_message
            )
    
    async def _check_exists(self, result: Any, error_message: str = "记录不存在") -> Any:
        """
        检查记录是否存在
        
        Args:
            result: 操作结果，通常是从数据库获取的记录
            error_message: 当记录不存在时的错误消息
            
        Returns:
            输入的结果值
            
        Raises:
            HTTPException: 当记录不存在时抛出404错误
        """
        if not result:
            raise HTTPException(
                status_code=404,
                detail=error_message
            )
        return result
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新记录
        
        Args:
            data: 要创建的记录数据字典
            
        Returns:
            Dict[str, Any]: 创建的记录数据
            
        Raises:
            HTTPException: 当创建失败时抛出500错误
            
        Notes:
            - 自动记录错误日志
            - 统一错误处理
        """
        return await self._handle_operation_error(
            self.repository.create,
            "创建记录",
            "创建记录失败",
            500,
            data=data
        )
    
    async def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        获取单条记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[Dict[str, Any]]: 记录数据，如果不存在则返回None
            
        Raises:
            HTTPException: 当记录不存在时抛出404错误，其他错误时抛出500错误
            
        Notes:
            - 自动处理记录不存在的情况
            - 记录所有错误
        """
        item = await self._handle_operation_error(
            self.repository.get,
            "获取记录",
            "获取记录失败",
            500,
            id=id
        )
        return await self._check_exists(item, "记录不存在")
    
    async def update(
        self,
        id: Any,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新记录
        
        Args:
            id: 记录ID
            data: 更新的数据字典
            
        Returns:
            Dict[str, Any]: 更新后的记录数据
            
        Raises:
            HTTPException: 当记录不存在时抛出404错误，更新失败时抛出500错误
            
        Notes:
            - 自动验证记录存在性
            - 记录所有错误
        """
        item = await self._handle_operation_error(
            self.repository.update,
            "更新记录",
            "更新记录失败",
            500,
            id=id, 
            data=data
        )
        return await self._check_exists(item, "记录不存在")
    
    async def delete(self, id: Any) -> None:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Raises:
            HTTPException: 当记录不存在时抛出404错误，删除失败时抛出500错误
            
        Notes:
            - 自动验证记录存在性
            - 记录所有错误
            - 成功删除不返回任何数据
        """
        result = await self._handle_operation_error(
            self.repository.delete,
            "删除记录",
            "删除记录失败",
            500,
            id=id
        )
        await self._check_exists(result, "记录不存在")
    
    async def restore(self, id: Any) -> None:
        """
        恢复已删除的记录
        
        Args:
            id: 记录ID
            
        Raises:
            HTTPException: 当记录不存在时抛出404错误，恢复失败时抛出500错误
            
        Notes:
            - 仅适用于已软删除的记录
            - 自动验证记录存在性
            - 记录所有错误
            - 成功恢复不返回任何数据
        """
        result = await self._handle_operation_error(
            self.repository.restore,
            "恢复记录",
            "恢复记录失败",
            500,
            id=id
        )
        await self._check_exists(result, "记录不存在或未被删除")
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """
        获取记录列表
        
        Args:
            filters: 过滤条件字典
            skip: 跳过的记录数
            limit: 返回的最大记录数
            sort_by: 排序字段
            order: 排序方向("asc"或"desc")
            
        Returns:
            List[Dict[str, Any]]: 记录列表
            
        Raises:
            HTTPException: 查询失败时抛出500错误
            
        Notes:
            - 支持分页查询
            - 支持过滤条件
            - 支持排序
            - 记录所有错误
        """
        return await self._handle_operation_error(
            self.repository.list,
            "获取记录列表",
            "获取记录列表失败",
            500,
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        获取记录数量
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            int: 符合条件的记录数量
            
        Raises:
            HTTPException: 查询失败时抛出500错误
            
        Notes:
            - 支持过滤条件
            - 记录所有错误
        """
        return await self._handle_operation_error(
            self.repository.count,
            "获取记录数量",
            "获取记录数量失败",
            500,
            filters=filters
        ) 