from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ChatCreate(BaseModel):
    user2_id: int

class ChatRead(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)