"""
Redis客户端模块

提供全局Redis连接实例，用于：
- 缓存管理
- 会话存储
- 速率限制
- 任务队列
- 实时消息

使用settings中的配置参数初始化连接。
所有响应都会自动解码为Python字符串。
"""

from redis import Redis
from ..core.config import settings

# 全局Redis客户端实例
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,  # 添加密码支持
    socket_timeout=settings.REDIS_TIMEOUT,  # 添加超时设置
    decode_responses=True,  # 自动解码响应为Python字符串
    health_check_interval=30,  # 定期检查连接健康状态
    retry_on_timeout=True,  # 超时时自动重试
    max_connections=10,  # 连接池最大连接数
    encoding='utf-8'  # 设置编码
) 

