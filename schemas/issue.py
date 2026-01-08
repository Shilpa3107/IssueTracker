from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .comment import CommentRead
from .label import LabelRead

# Request model to create an issue
class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None  # optional

# Request model to update an issue
class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    version: int  # required for optimistic concurrency check

# Response model for returning issue info
class IssueRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    assignee_id: Optional[int]
    version: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    comments: List[CommentRead] = []
    labels: List[LabelRead] = []

    class Config:
        orm_mode = True
