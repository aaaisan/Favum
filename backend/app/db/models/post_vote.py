from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from ...core.enums import VoteType

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
        # 确保每个用户对一个帖子只有一个投票记录
        UniqueConstraint('post_id', 'user_id', name='uix_user_post_vote'),
    ) 