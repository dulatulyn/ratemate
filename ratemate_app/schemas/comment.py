from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime

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

class CommentRead(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: str
    created_at: datetime
    parent_id: int | None = None

    model_config = ConfigDict(from_attributes=True)