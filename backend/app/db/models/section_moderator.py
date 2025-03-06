from sqlalchemy import Column, Integer, ForeignKey, Boolean
from datetime import datetime

from .base import Base

class SectionModerator(Base):
    __tablename__ = "section_moderators"
    
    section_id = Column(Integer, ForeignKey("sections.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记 