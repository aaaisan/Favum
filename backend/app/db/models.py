from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, Table, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from datetime import datetime, timezone, timedelta
import enum
import sqlalchemy

CHINA_TZ = timezone(timedelta(hours=8))
Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

# 点赞类型枚举
class VoteType(str, enum.Enum):
    UPVOTE = "upvote"    # 点赞
    DOWNVOTE = "downvote"  # 反对

# 帖子-标签关联表
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

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

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, index=True)
    post_count = Column(Integer, default=0)  # 使用该标签的帖子数量
    created_at = Column(DateTime, default=datetime.now)
    last_used_at = Column(DateTime, nullable=True)  # 最后一次使用时间
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    
    posts = relationship("Post", secondary=post_tags, back_populates="tags")

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记
    
    posts = relationship("Post", back_populates="section")
    moderators = relationship("User", secondary="section_moderators")

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

class SectionModerator(Base):
    __tablename__ = "section_moderators"
    
    section_id = Column(Integer, ForeignKey("sections.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    is_deleted = Column(Boolean, default=False)  # 添加软删除标记

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

# 添加帖子点赞表
class PostVote(Base):
    __tablename__ = "post_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    vote_type = Column(String(10), default=VoteType.UPVOTE)  # 点赞类型：点赞/反对
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="post_votes")
    post = relationship("Post", back_populates="votes")
    
    __table_args__ = (
        # 添加唯一约束，确保一个用户对一个帖子只能有一个投票记录
        sqlalchemy.UniqueConstraint('post_id', 'user_id', name='uix_post_user'),
    )

# 添加帖子收藏表
class PostFavorite(Base):
    __tablename__ = "post_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="favorites")
    post = relationship("Post", back_populates="favorited_by")
    
    __table_args__ = (
        # 添加唯一约束，确保一个用户对一个帖子只能有一条收藏记录
        sqlalchemy.UniqueConstraint('post_id', 'user_id', name='uix_post_user_favorite'),
    )