from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    deleted_at = Column(DateTime, nullable=True)  # 记录删除时间
    
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments") 