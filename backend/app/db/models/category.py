from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    order = Column(Integer, default=0)  # 排序字段，数字越小越靠前
    created_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    
    # 自引用关系
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Category.order"  # 子分类按 order 排序
    )
    parent = relationship("Category", back_populates="children", remote_side=[id])
    posts = relationship("Post", back_populates="category") 