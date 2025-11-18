from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime

class RatingCreate(BaseModel):
    post_id: int | None = None
    score: int = Field(ge=0, le=10)
    @model_validator(mode="after")
    def validate_target(self):
        if(self.post_id is None) == (self.comment_id is None):
            raise ValueError("Provide exactly one of post_id or comment_id")
        return self

class RatingRead(BaseModel):
    id: int
    user_id: int
    post_id: int | None = None
    comment_id: int | None = None
    score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RatingSummary(BaseModel):
    post_id: int
    average: float
    count: int