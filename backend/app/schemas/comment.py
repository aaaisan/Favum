from pydantic import BaseModel
from datetime import datetime

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    author_id: int
    post_id: int

class CommentUpdate(BaseModel):
    content: str

class Comment(CommentBase):
    id: int
    author_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True 