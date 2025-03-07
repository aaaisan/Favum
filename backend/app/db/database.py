from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..core.config import settings
from ..core.logging import get_logger

# 导入从models/base.py中的Base
from .models.base import Base

logger = get_logger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_size=settings.DB_POOL_SIZE,  # 连接池大小
    max_overflow=settings.DB_MAX_OVERFLOW,  # 最大溢出连接数
    pool_timeout=settings.DB_POOL_TIMEOUT,  # 连接池超时时间
    pool_recycle=settings.DB_POOL_RECYCLE,  # 连接回收时间
    echo=settings.DB_ECHO  # SQL语句日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def transaction_context() -> Generator[Session, None, None]:
    """事务上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"数据库事务失败: {str(e)}")
        raise
    finally:
        db.close()

def check_database_connection() -> bool:
    """检查数据库连接是否正常"""
    try:
        with transaction_context() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {str(e)}")
        return False

def init_db() -> None:
    """
    初始化数据库
    - 创建所有表
    - 创建初始数据（如果需要）
    """
    # 这里导入所有模型，确保它们被注册到Base的metadata中
    from .models import User, Post, Comment, Category, Tag, Section, SectionModerator, PostVote, PostFavorite
    
    Base.metadata.create_all(bind=engine)