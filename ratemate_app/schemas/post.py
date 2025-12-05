from pydantic import BaseModel, field_validator, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from ratemate_app.schemas.media import MediaRead

class PostBase(BaseModel):
    title: Optional[str] = None
    content: str

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content must not be empty')
        return v
    
class PostCreate(PostBase):
    pass

class PostRead(PostBase):
    id: int
    owner_id: int
    title: Optional[str] = None
    content: str
    created_at: datetime
    media: list[MediaRead] = []
    media_urls: list[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('media_urls')
    def _ser_media_urls(self, v):
        return v if v else [m.url for m in getattr(self, 'media', [])]