from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None

class Tag(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 