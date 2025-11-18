from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FollowCreate(BaseModel):
    followed_id: int

class FollowRead(BaseModel):
    id: int
    follower_id: int
    followed_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)