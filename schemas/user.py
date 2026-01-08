from pydantic import BaseModel, EmailStr
from datetime import datetime

# Request model when creating a user
class UserCreate(BaseModel):
    name: str
    email: EmailStr

# Response model for returning user info
class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True  # tells Pydantic to read data from ORM objects
