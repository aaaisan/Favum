import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    """
    启动后端服务
    
    使用 uvicorn 启动 FastAPI 应用，监听 0.0.0.0:8000
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    print(f"应用已启动，访问 http://127.0.0.1:8000{settings.API_V1_STR}/docs 查看API文档") 