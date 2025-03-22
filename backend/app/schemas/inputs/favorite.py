from pydantic import BaseModel

class FavoriteSchema(BaseModel):
    post_id: int
    user_id: int



