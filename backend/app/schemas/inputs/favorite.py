from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    post_id: int
    user_id: int

class FavoriteDelete(BaseModel):
    post_id: int
    user_id: int

