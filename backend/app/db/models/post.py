from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from .post_tag import post_tags

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_hidden = Column(Boolean, default=False)  # 是否隐藏，默认为False
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    deleted_at = Column(DateTime, nullable=True)  # 记录删除时间
    vote_count = Column(Integer, default=0)  # 添加点赞计数字段
    
    author = relationship("User", back_populates="posts")
    section = relationship("Section", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    votes = relationship("PostVote", back_populates="post")
    favorited_by = relationship("PostFavorite", back_populates="post")  # 添加被收藏关系 