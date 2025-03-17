from pydantic import BaseModel
from typing import Optional, List

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    # 其他需要的字段
    
    class Config:
        orm_mode = True 