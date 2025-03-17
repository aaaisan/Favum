from pydantic import BaseModel
from typing import Optional, List

class FavoriteResponse(BaseModel):
    user_id: int
    post_id: int

class FavoriteListResponse(FavoriteResponse):
    Favorites: Optional[List[FavoriteResponse]]