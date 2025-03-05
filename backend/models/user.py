from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    avatar = Column(String(255), nullable=True)
    role = Column(String(20), default="user")  # admin, moderator, user
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    
    # 虚拟字段，非数据库字段
    # 这些在FastAPI Pydantic模型中处理
    # post_count
    # comment_count
    # like_count
    # follower_count
    # following_count 