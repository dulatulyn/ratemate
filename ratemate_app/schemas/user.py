from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime
import re

class UserBase(BaseModel):
    username: str
    email: EmailStr

    @field_validator('username')
    @classmethod
    def validate(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', v):
            raise ValueError('Username must be 3-30 characters long with no special symbols')
        return v
    
class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class UserSummary(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)