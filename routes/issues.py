from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.issue import Issue, IssueStatus
from schemas.issue import IssueCreate, IssueUpdate, IssueRead
from services.issue_service import (
    create_issue,
    update_issue,
    replace_labels,
    bulk_status_update,
    import_issues_csv,
    get_issue_timeline
)

router = APIRouter(prefix="/issues", tags=["Issues"])

# CREATE ISSUE
@router.post("/", response_model=IssueRead, status_code=201)
def api_create_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    try:
        return create_issue(db, issue.title, issue.description, issue.assignee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# LIST ISSUES (Filter + Pagination)
@router.get("/", response_model=List[IssueRead])
def api_list_issues(
    status: Optional[IssueStatus] = None,
    assignee_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    query = db.query(Issue)
    if status:
        query = query.filter(Issue.status == status)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    
    return query.offset(skip).limit(limit).all()

# GET ISSUE
@router.get("/{issue_id}", response_model=IssueRead)
def api_get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

# UPDATE ISSUE
@router.patch("/{issue_id}", response_model=IssueRead)
def api_update_issue(issue_id: int, issue: IssueUpdate, db: Session = Depends(get_db)):
    try:
        return update_issue(db, issue_id, issue.dict(exclude_unset=True))
    except ValueError as e:
        if "Version conflict" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# REPLACE LABELS
@router.put("/{issue_id}/labels", response_model=IssueRead)
def api_replace_labels(issue_id: int, labels: List[str], db: Session = Depends(get_db)):
    try:
        return replace_labels(db, issue_id, labels)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# BULK STATUS UPDATE
@router.post("/bulk-status")
def api_bulk_status_update(updates: List[dict], db: Session = Depends(get_db)):
    try:
        bulk_status_update(db, updates)
        return {"detail": "Bulk status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# CSV IMPORT
@router.post("/import")
def api_import_issues(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8")
    return import_issues_csv(db, content)

# BONUS: TIMELINE
@router.get("/{issue_id}/timeline")
def api_get_timeline(issue_id: int, db: Session = Depends(get_db)):
    timeline = get_issue_timeline(db, issue_id)
    if not timeline and not db.query(Issue).filter(Issue.id == issue_id).first():
         raise HTTPException(status_code=404, detail="Issue not found")
    return [{"action": t.action, "timestamp": t.timestamp} for t in timeline]
