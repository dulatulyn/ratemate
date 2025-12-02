from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta

class LowkeyCreate(BaseModel):
    title: str | None = None

class LowkeyRead(BaseModel):
    id: int
    owner_id: int
    title: str | None = None
    media_url: str | None = None
    media_type: str | None = None
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LowkeyViewRead(BaseModel):
    viewer_id: int
    username: str
    viewed_at: datetime