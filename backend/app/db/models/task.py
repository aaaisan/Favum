from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped

from ..database import Base

class Task(Base):
    """任务模型"""
    
    __tablename__ = "tasks"
    
    name: Mapped[str] = Column(String(100), primary_key=True)
    type: Mapped[str] = Column(String(50), index=True)
    description: Mapped[str] = Column(Text, nullable=True)
    interval: Mapped[int] = Column(Integer, nullable=True)
    max_retries: Mapped[int] = Column(Integer, default=3)
    retry_delay: Mapped[int] = Column(Integer, default=5)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
    last_run: Mapped[datetime] = Column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = Column(Boolean, default=False)
    deleted_at: Mapped[datetime] = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "interval": self.interval,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        } 