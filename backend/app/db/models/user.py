from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, UserRole

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 添加更新时间字段
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    deleted_at = Column(DateTime, nullable=True)  # 记录删除时间
    
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    moderated_sections = relationship("Section", secondary="section_moderators")
    post_votes = relationship("PostVote", back_populates="user")
    favorites = relationship("PostFavorite", back_populates="user")  # 添加用户收藏关系
    
    # 虚拟字段，非数据库字段
    # 这些在FastAPI Pydantic模型中处理
    # post_count
    # comment_count
    # like_count
    # follower_count
    # following_count 