from pydantic import BaseModel, field_validator, ConfigDict, field_serializer
from datetime import datetime
from ratemate_app.schemas.media import MediaRead

class CommentCreate(BaseModel):
    post_id: int
    content: str
    parent_id: int | None = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content must not be empty')
        return v

    @field_validator('parent_id')
    @classmethod
    def normalize_parent_id(cls, v: int | None):
        if v is None:
            return None
        if v <= 0:
            return None
        return v

class CommentRead(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: str
    created_at: datetime
    parent_id: int | None = None
    media: list[MediaRead] = []
    media_urls: list[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('media_urls')
    def _ser_media_urls(self, v):
        return v if v else [m.urls for m in getattr(self, 'media', [])]

class RatingRequest(BaseModel):
    score: int

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Score must be between 1 and 10")
        return v

class RatingResponse(BaseModel):
    success: bool

    