from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.issue_service import top_assignees, average_resolution_time

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/top-assignees")
def api_top_assignees(limit: int = 5, db: Session = Depends(get_db)):
    result = top_assignees(db, limit)
    return [{"assignee": r[0], "issue_count": r[1]} for r in result]

@router.get("/latency")
def api_average_resolution_time(db: Session = Depends(get_db)):
    avg_hours = average_resolution_time(db)
    return {"average_resolution_time_hours": round(avg_hours, 2)}
