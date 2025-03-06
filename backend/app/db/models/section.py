from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    
    posts = relationship("Post", back_populates="section")
    moderators = relationship("User", secondary="section_moderators") 