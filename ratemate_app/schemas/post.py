from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

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

    model_config = ConfigDict(from_attributes=True)