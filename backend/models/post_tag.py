from sqlalchemy import Table, Column, Integer, ForeignKey
from database import Base

# 帖子-标签多对多关系表
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
) 