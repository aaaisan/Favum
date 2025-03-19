from pydantic import BaseModel
from typing import Optional, List

class FavoriteResponse(BaseModel):
    user_id: int
    post_id: int

class FavoriteListResponse(BaseModel):
    favorites: Optional[List[FavoriteResponse]]
    total: int

class FavoriteDetailResponse(BaseModel):
    favorite: FavoriteResponse

class FavoriteDeleteResponse(BaseModel):
    message: str
