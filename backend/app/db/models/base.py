from __future__ import annotations
# from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, Table, func
# from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, Table, func
from sqlalchemy.orm import declarative_base
from datetime import timezone, timedelta
# from datetime import datetime, timezone, timedelta
import enum

# 中国时区，用于datetime默认值
CHINA_TZ = timezone(timedelta(hours=8))

# 声明SQLAlchemy基类
Base = declarative_base()

# 用户角色枚举
# class UserRole(str, enum.Enum):
#     ADMIN = "admin"
#     MODERATOR = "moderator"
#     USER = "user"

# # 点赞类型枚举
# class VoteType(str, enum.Enum):
#     UPVOTE = "upvote"    # 点赞
#     DOWNVOTE = "downvote"  # 反对 