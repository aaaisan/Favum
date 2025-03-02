from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import logging

from ...core.decorators import (
    handle_exceptions,
    rate_limit,
    cache,
    validate_token,
    log_execution_time
)
from ...core.base_service import BaseService
from sqlalchemy.exc import SQLAlchemyError

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