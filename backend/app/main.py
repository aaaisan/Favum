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
from .core.database import init_db
from .core.logging import setup_logging, get_logger
from .core.cache import RedisClient, cache_manager
from jose import jwt  # 导入jwt模块
from .middlewares import add_error_handler
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# 配置日志
logging.basicConfig(
    level=logging.ERROR,  # 只记录错误级别的日志
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 初始化数据库
init_db()

# 定义允许的CORS源
origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    "*"
]

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
        description="论坛 API 接口文档\n\n### 认证说明\n1. 首先使用 `/api/v1/auth/swagger-auth` 端点获取JWT令牌\n2. 点击右上角的 'Authorize' 按钮\n3. 在弹出的对话框中输入 `Bearer your_jwt_token` (替换为您的实际令牌)\n4. 点击 'Authorize' 按钮完成认证",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
        generate_unique_id_function=custom_generate_unique_id,  # 自定义操作ID生成
        redirect_slashes=False, 
        swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect", # 禁用路径尾部斜杠的自动重定向
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": False,
            "clientId": "swagger",
            "clientSecret": "",
            "appName": "Swagger UI"
        },
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # 隐藏默认模型
            "persistAuthorization": True,    # 保持认证状态
            "displayRequestDuration": True,  # 显示请求持续时间
            "docExpansion": "list",          # 展开操作列表
            "filter": True                   # 启用过滤功能
        }
    )

    # CORS 中间件已在 middleware.py 中配置
    
    # 设置中间件
    setup_middleware(app)
    
    # 添加全局错误处理
    add_error_handler(app)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 添加JWT模块到应用状态
    app.state.jwt = jwt
    
    # 添加自定义的安全方案定义
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    
    # 更新OpenAPI配置，添加API密钥安全方案
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # 添加API密钥认证方案
        openapi_schema["components"]["securitySchemes"]["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "输入格式: **Bearer your_jwt_token**"
        }
        
        # 添加全局安全配置
        openapi_schema["security"] = [
            {"OAuth2PasswordBearer": []},
            {"ApiKeyAuth": []}
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
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