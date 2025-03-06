from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class PostFavorite(Base):
    __tablename__ = "post_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="favorites")
    post = relationship("Post", back_populates="favorited_by")
    
    __table_args__ = (
        # 确保每个用户对一个帖子只有一个收藏记录
        UniqueConstraint('post_id', 'user_id', name='uix_user_post_favorite'),
    ) 