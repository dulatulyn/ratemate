from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime

class MediaCreate(BaseModel):
    post_id: int
    url: str
    media_type: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('URL must not be empty')
        return v

class MediaRead(BaseModel):
    id: int
    post_id: int | None = None
    comment_id: int | None = None
    url: str
    media_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)