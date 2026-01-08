from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.comment import CommentCreate, CommentRead
from services.issue_service import add_comment

router = APIRouter(prefix="/issues/{issue_id}/comments", tags=["Comments"])

@router.post("/", response_model=CommentRead, status_code=201)
def api_add_comment(issue_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    try:
        return add_comment(db, issue_id, comment.author_id, comment.body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
