"""
应用程序主入口

配置和启动FastAPI应用程序
"""

from __future__ import annotations
import logging
from fastapi import FastAPI
from .core.config import settings
from .core.middleware import setup_middleware
from .api.router import api_router
from .db.database import init_db
from .core.logging import setup_logging, get_logger
from .core.cache import RedisClient, cache_manager
from jose import jwt  # 导入jwt模块
from .middleware.error_handler import add_error_handler
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 初始化数据库
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        # 异步初始化 Redis 并添加到应用状态
        app.state.redis = await RedisClient.get_instance()
        
        # 初始化缓存管理器
        await cache_manager.initialize()
        
        logger.info("应用初始化成功: Redis连接已建立")
    except Exception as e:
        logger.critical(f"应用初始化失败: {str(e)}", 
                       extra={
                           "error_type": e.__class__.__name__,
                           "details": str(e)
                       })
    
    yield  # 这里是应用正常运行的时间点
    
    # 关闭Redis连接
    if hasattr(app.state, "redis") and app.state.redis:
        logger.info("正在关闭Redis连接...")
        await app.state.redis.close()
        logger.info("Redis连接已关闭")

def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用
    
    Returns:
        配置好的FastAPI应用实例
    """
    
    # 自定义操作ID生成函数，避免使用函数签名（包含Callable等不兼容类型）
    def custom_generate_unique_id(route):
        # 使用路径和方法作为唯一标识，而不是包含函数签名
        tag = route.tags[0] if route.tags else 'default'
        path = route.path.replace("/", "_").replace("{", "").replace("}", "")
        method = next(iter(route.methods)) if route.methods else "get"
        return f"{tag}__{method}__{path}"
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="论坛 API 接口文档",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
        generate_unique_id_function=custom_generate_unique_id,  # 自定义操作ID生成
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # 使用配置中的允许源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的方法
        allow_headers=["*"],  # 允许所有头部
        expose_headers=["X-Request-ID", "X-Process-Time"],  # 只暴露必要的头部
        max_age=3600,
    )
    
    # 设置中间件
    setup_middleware(app)
    
    # 添加全局错误处理
    add_error_handler(app)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 添加JWT模块到应用状态
    app.state.jwt = jwt
    
    return app

app = create_app()

@app.get("/")
async def root():
    """应用根路径处理函数"""
    return {
        "message": "欢迎访问论坛 API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }