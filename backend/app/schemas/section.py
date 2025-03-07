from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SectionBase(BaseModel):
    name: str
    description: str

class SectionCreate(SectionBase):
    pass

class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Section(SectionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 