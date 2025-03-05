from typing import List, Optional, Union, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, EmailStr, field_validator, model_validator
from pathlib import Path
import logging
import secrets
import urllib.parse

"""
应用配置模块

使用pydantic_settings管理应用配置。
支持从环境变量和.env文件加载配置。
提供了完整的类型提示和验证。

配置项包括：
- API配置：版本、名称等
- 安全配置：密钥、令牌等
- 数据库配置：MySQL连接参数
- Redis配置：缓存和消息队列
- 日志配置：格式、路径等
- 邮件配置：SMTP服务器参数
- 性能配置：限流、监控等
"""

class Settings(BaseSettings):
    """
    应用配置类
    
    集中管理所有应用配置项，支持环境变量覆盖。
    所有配置项都提供类型提示和默认值（如果适用）。
    
    配置加载优先级：
    1. 环境变量
    2. .env文件
    3. 默认值
    """
    
    # Pydantic配置
    model_config = {
        "extra": "allow",  # 允许额外字段
        "case_sensitive": True,  # 配置键大小写敏感
        "env_file": ".env",  # 环境变量文件路径
        "env_file_encoding": "utf-8",  # 环境变量文件编码
    }
    
    # API配置
    API_V1_STR: str = "/api/v1"
    """API版本前缀"""
    
    PROJECT_NAME: str = "Forum API"
    """项目名称"""
    
    VERSION: str = "1.0.0"
    """API版本号"""
    
    DESCRIPTION: str = "现代化论坛API系统"
    """项目描述"""
    
    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    """
    用于加密的密钥
    默认在启动时自动生成32字节的随机密钥
    """
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    """访问令牌过期时间（分钟）"""
    
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    """刷新令牌过期时间（分钟）"""
    
    ALGORITHM: str = "HS256"
    """JWT加密算法"""
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React 默认端口
        "http://127.0.0.1:3000", 
        "http://localhost:5000",  # Flask 默认端口
        "http://127.0.0.1:5000",
        "http://localhost:4200",  # Angular 默认端口
        "http://127.0.0.1:4200",
        "http://localhost:9000",  # 常见开发端口
        "http://127.0.0.1:9000",
        "http://localhost:5174",  # Vite 可能的替代端口
        "http://127.0.0.1:5174",
        "http://localhost:4000",  # 常见开发端口
        "http://127.0.0.1:4000",
        "http://localhost:4173",  # Vite 预览模式端口
        "http://127.0.0.1:4173",
        "http://localhost",       # 无端口时
        "http://127.0.0.1",       # 无端口时
    ]
    """
    允许的CORS源
    可以是URL列表或逗号分隔的URL字符串
    """

    # 开发环境中允许所有源
    CORS_ORIGINS: List[str] = ["*"]
    """允许的CORS源，开发环境中允许所有源"""
    
    ALLOWED_HOSTS: List[str] = ["*"]
    """允许的主机名列表"""
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        处理CORS源配置
        
        支持以下格式：
        - URL列表
        - 逗号分隔的URL字符串
        - 单个URL字符串
        
        Args:
            v: 输入的CORS配置值
            
        Returns:
            List[str]: 处理后的CORS源列表
            
        Raises:
            ValueError: 当输入格式无效时抛出
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    MYSQL_USER: str
    """MySQL用户名"""
    
    MYSQL_PASSWORD: str
    """MySQL密码"""
    
    MYSQL_HOST: str = "localhost"
    """MySQL主机地址"""
    
    MYSQL_PORT: int = 3306
    """MySQL端口号"""
    
    MYSQL_DATABASE: str
    """MySQL数据库名"""
    
    DB_ECHO: bool = False
    """是否打印SQL语句，用于调试"""
    
    DB_POOL_SIZE: int = 5
    """数据库连接池大小"""
    
    DB_MAX_OVERFLOW: int = 10
    """连接池最大溢出连接数"""
    
    DB_POOL_TIMEOUT: int = 30
    """连接池获取超时时间（秒）"""
    
    DB_POOL_RECYCLE: int = 3600
    """连接回收时间（秒）"""
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    """Redis主机地址"""
    
    REDIS_PORT: int = 6379
    """Redis端口号"""
    
    REDIS_DB: int = 0
    """Redis数据库索引"""
    
    REDIS_PASSWORD: Optional[str] = None
    """Redis密码，可选"""
    
    REDIS_TIMEOUT: int = 5
    """Redis连接超时时间（秒）"""
    
    # 缓存配置
    CACHE_EXPIRE_MINUTES: int = 60
    """通用缓存过期时间（分钟）"""
    
    USER_CACHE_EXPIRE: int = 3600
    """用户信息缓存过期时间（秒）"""
    
    # 验证码配置
    CAPTCHA_EXPIRE_MINUTES: int = 5
    """验证码有效期（分钟）"""
    
    CAPTCHA_LENGTH: int = 6
    """验证码长度"""
    
    CAPTCHA_WIDTH: int = 200
    """验证码图片宽度（像素）"""
    
    CAPTCHA_HEIGHT: int = 60
    """验证码图片高度（像素）"""
    
    # 速率限制配置
    RATE_LIMIT_REQUESTS: int = 1000000
    """速率限制请求次数"""
    
    RATE_LIMIT_WINDOW: int = 3600
    """速率限制时间窗口（秒）"""
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    """日志级别"""
    
    LOG_FORMAT: str = "json"
    """日志格式（json或text）"""
    
    LOG_PATH: Path = Path("logs")
    """日志文件目录"""
    
    LOG_FILE: Path = LOG_PATH / "app.log"
    """主日志文件路径"""
    
    LOG_ROTATION: str = "daily"
    """日志轮转方式（daily或size）"""
    
    LOG_MAX_SIZE: int = 10 * 1024 * 1024
    """单个日志文件最大大小（字节）"""
    
    LOG_BACKUP_COUNT: int = 30
    """保留的日志文件数量"""
    
    LOG_ERRORS_TO_FILE: bool = True
    """是否将错误日志单独写入文件"""
    
    # 性能监控配置
    SLOW_API_THRESHOLD: float = 0.5
    """慢API请求阈值（秒）"""
    
    # Celery配置
    CELERY_BROKER_URL: Optional[str] = None
    """Celery消息代理URL"""
    
    CELERY_RESULT_BACKEND: Optional[str] = None
    """Celery结果后端URL"""
    
    CELERY_TASK_SERIALIZER: str = "json"
    """Celery任务序列化格式"""
    
    CELERY_RESULT_SERIALIZER: str = "json"
    """Celery结果序列化格式"""
    
    CELERY_ACCEPT_CONTENT: Union[List[str], str] = ["json"]
    """Celery接受的内容类型"""
    
    @field_validator("CELERY_ACCEPT_CONTENT", mode="before")
    def parse_celery_accept_content(cls, v):
        """处理CELERY_ACCEPT_CONTENT配置项"""
        if isinstance(v, str):
            # 处理字符串格式，如果是逗号分隔的列表则拆分
            if "," in v:
                return [item.strip() for item in v.split(",")]
            # 处理单个值
            return [v.strip()]
        return v
    
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    """Celery时区设置"""
    
    CELERY_ENABLE_UTC: bool = True
    """Celery是否启用UTC"""
    
    @field_validator("CELERY_ENABLE_UTC", "CELERY_TASK_TRACK_STARTED", "DB_ECHO", "MAIL_TLS", "MAIL_SSL", "LOG_ERRORS_TO_FILE", "BACKUP_COMPRESS", mode="before")
    def parse_bool(cls, v):
        """处理布尔值配置项"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y")
        return v
    
    CELERY_TASK_TRACK_STARTED: bool = True
    """是否跟踪任务开始状态"""
    
    CELERY_TASK_TIME_LIMIT: int = 1800
    """任务执行时间限制（秒）"""
    
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    """每个worker处理的最大任务数"""
    
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    """worker预取任务乘数"""
    
    # 邮件配置
    MAIL_USERNAME: str
    """SMTP用户名"""
    
    MAIL_PASSWORD: str
    """SMTP密码"""
    
    MAIL_FROM: EmailStr
    """发件人邮箱"""
    
    MAIL_PORT: int = 587
    """SMTP端口"""
    
    MAIL_SERVER: str
    """SMTP服务器地址"""
    
    MAIL_TLS: bool = True
    """是否使用TLS"""
    
    MAIL_SSL: bool = False
    """是否使用SSL"""
    
    MAIL_FROM_NAME: Optional[str] = None
    """发件人显示名称"""
    
    # 备份配置
    BACKUP_DIR: Path = Path("backups")
    """备份文件目录"""
    
    BACKUP_KEEP_DAYS: int = 7
    """备份文件保留天数"""
    
    BACKUP_COMPRESS: bool = True
    """是否压缩备份文件"""
    
    # 自定义URL生成方法
    def _get_redis_url(self) -> str:
        """
        生成Redis连接URL
        
        使用配置的Redis参数构建连接URL，确保密码中的特殊字符被正确编码
        
        Returns:
            str: 完整的Redis连接URL
        """
        # 对密码进行URL编码以处理特殊字符（如@将被转换为%40）
        encoded_password = urllib.parse.quote_plus(self.REDIS_PASSWORD) if self.REDIS_PASSWORD else ""
        
        # 构建认证部分
        auth_part = ""
        if encoded_password:
            auth_part = ":" + encoded_password + "@"
            
        # 使用字符串拼接方式，避免格式化字符串中的%问题
        return "redis://" + auth_part + self.REDIS_HOST + ":" + str(self.REDIS_PORT) + "/" + str(self.REDIS_DB)
    
    @property
    def DATABASE_URL(self) -> str:
        """
        获取数据库URL
        
        根据配置的MySQL参数生成SQLAlchemy连接URL
        
        Returns:
            str: 完整的数据库连接URL
        """
        # 对密码进行URL编码以处理特殊字符
        encoded_password = urllib.parse.quote_plus(self.MYSQL_PASSWORD)
        
        # 使用字符串拼接方式，避免格式化字符串中的%问题
        return "mysql+pymysql://" + self.MYSQL_USER + ":" + encoded_password + "@" + self.MYSQL_HOST + ":" + str(self.MYSQL_PORT) + "/" + self.MYSQL_DATABASE
    
    def __init__(self, **kwargs):
        """初始化设置并设置Celery URL"""
        super().__init__(**kwargs)
        
        # 如果没有显式设置Celery URL，则使用Redis URL
        redis_url = self._get_redis_url()
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = redis_url
            
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = redis_url

# 创建设置实例
settings = Settings()

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
