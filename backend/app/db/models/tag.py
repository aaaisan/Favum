from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from .post_tag import post_tags

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, index=True)
    post_count = Column(Integer, default=0)  # 使用该标签的帖子数量
    created_at = Column(DateTime, default=datetime.now)
    last_used_at = Column(DateTime, nullable=True)  # 最后一次使用时间
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    
    # 关系
    posts = relationship("Post", secondary=post_tags, back_populates="tags") 