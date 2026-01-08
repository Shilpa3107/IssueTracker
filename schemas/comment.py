from pydantic import BaseModel
from datetime import datetime

class CommentCreate(BaseModel):
    author_id: int
    body: str

class CommentRead(BaseModel):
    id: int
    issue_id: int
    author_id: int
    body: str
    created_at: datetime

    class Config:
        orm_mode = True
