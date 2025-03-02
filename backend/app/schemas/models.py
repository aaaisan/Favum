from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# 用户相关模型
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# 帖子相关模型
class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# 评论相关模型
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    post_id: int

class CommentResponse(CommentBase):
    id: int
    author_id: int
    post_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True