from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel
import logging
from sqlalchemy.exc import SQLAlchemyError

# 修改导入方式，从各个子模块导入
from ...core.decorators.error import handle_exceptions
from ...core.decorators.performance import rate_limit, cache, endpoint_rate_limit
from ...core.decorators.auth import validate_token, require_roles, require_permissions
from ...core.decorators.logging import log_execution_time
from ...core.base_service import BaseService

class BaseEndpoint:
    """基础API端点"""
    
    def __init__(
        self,
        *,
        router: APIRouter,
        prefix: str,
        tags: List[str],
        service: Type[BaseService],
        response_model: Optional[Type[BaseModel]] = None,
        create_schema: Optional[Type[BaseModel]] = None,
        update_schema: Optional[Type[BaseModel]] = None
    ):
        self.router = router
        self.prefix = prefix
        self.tags = tags
        self.service = service()
        self.response_model = response_model
        self.create_schema = create_schema
        self.update_schema = update_schema
        
        self.register_routes()
    
    def register_routes(self) -> None:
        """注册路由"""
        
        @self.router.post(
            self.prefix,
            response_model=self.response_model,
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="创建失败", include_details=True)
        @validate_token
        @rate_limit(limit=100, window=60)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def create(
            request: Request,
            data: self.create_schema
        ) -> Dict[str, Any]:
            """创建记录"""
            return await self.service.create(data.dict())
        
        @self.router.get(
            f"{self.prefix}/{{id}}",
            response_model=self.response_model,
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="获取失败", include_details=True)
        @validate_token
        @cache(expire=300, include_query_params=True)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def get(request: Request, id: Any) -> Dict[str, Any]:
            """获取记录"""
            return await self.service.get(id)
        
        @self.router.put(
            f"{self.prefix}/{{id}}",
            response_model=self.response_model,
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="更新失败", include_details=True)
        @validate_token
        @rate_limit(limit=100, window=60)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def update(
            request: Request,
            id: Any,
            data: self.update_schema
        ) -> Dict[str, Any]:
            """更新记录"""
            return await self.service.update(id, data.dict())
        
        @self.router.delete(
            f"{self.prefix}/{{id}}",
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="删除失败", include_details=True)
        @validate_token
        @rate_limit(limit=50, window=60)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def delete(request: Request, id: Any) -> Dict[str, Any]:
            """删除记录"""
            await self.service.delete(id)
            return {"message": "删除成功"}
        
        @self.router.post(
            f"{self.prefix}/{{id}}/restore",
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="恢复失败", include_details=True)
        @validate_token
        @rate_limit(limit=20, window=60)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def restore(request: Request, id: Any) -> Dict[str, Any]:
            """恢复记录"""
            await self.service.restore(id)
            return {"message": "恢复成功"}
        
        @self.router.get(
            self.prefix,
            response_model=List[self.response_model],
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="获取列表失败", include_details=True)
        @validate_token
        @cache(expire=60, include_query_params=True)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def list_all(
            request: Request, 
            skip: int = 0, 
            limit: int = 100
        ) -> List[Dict[str, Any]]:
            """获取记录列表"""
            return await self.service.list_all(skip=skip, limit=limit)
        
        @self.router.get(
            f"{self.prefix}/count",
            tags=self.tags
        )
        @handle_exceptions(SQLAlchemyError, status_code=500, message="获取数量失败", include_details=True)
        @validate_token
        @cache(expire=60, include_query_params=True)
        @log_execution_time(level=logging.INFO, message="{function_name} 执行完成，耗时 {execution_time:.3f}秒")
        async def count(request: Request) -> Dict[str, int]:
            """获取记录总数"""
            count = await self.service.count()
            return {"count": count}
        
        # 注册自定义端点
        self.register_custom_endpoints()
    
    def register_custom_endpoints(self) -> None:
        """注册自定义端点，子类可重写此方法添加额外端点"""
        pass

router = APIRouter()

@router.get("/example")
@endpoint_rate_limit(limit=30, window=60)  # 每分钟最多30个请求
async def example_endpoint(request: Request):
    """
    示例端点，演示特定端点的限流功能
    
    此端点使用endpoint_rate_limit装饰器限制请求频率为每分钟30次。
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        dict: 示例响应
    """
    return {"message": "这是一个示例API端点"} 