from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.issue import Issue, IssueStatus, IssueHistory
from models.user import User
from models.label import Label, issue_labels
from models.comment import Comment
from typing import List, Dict, Optional
from datetime import datetime
import csv
from io import StringIO
from sqlalchemy import func

# -----------------------------
# ISSUE CRUD & VERSION CONTROL
# -----------------------------

def create_issue(db: Session, title: str, description: str = None, assignee_id: int = None):
    # Validate assignee exists
    if assignee_id:
        user = db.query(User).filter(User.id == assignee_id).first()
        if not user:
            raise ValueError("Assignee not found")
    
    issue = Issue(title=title, description=description, assignee_id=assignee_id)
    db.add(issue)
    db.flush() # get ID
    
    history = IssueHistory(issue_id=issue.id, action="Issue created")
    db.add(history)
    
    db.commit()
    db.refresh(issue)
    return issue

def update_issue(db: Session, issue_id: int, data: dict):
    issue = db.query(Issue).filter(Issue.id == issue_id).with_for_update().first()
    if not issue:
        raise ValueError("Issue not found")

    if "version" in data and data["version"] != issue.version:
        raise ValueError("Version conflict")

    old_status = issue.status
    for key in ["title", "description", "status", "assignee_id"]:
        if key in data and data[key] is not None:
            val = data[key]
            if key == "status":
                val = IssueStatus.from_str(val)
            setattr(issue, key, val)


    if issue.status != old_status:
        history = IssueHistory(issue_id=issue.id, action=f"Status changed from {old_status} to {issue.status}")
        db.add(history)

    if data.get("status") == IssueStatus.DONE:
        issue.resolved_at = datetime.utcnow()

    issue.version += 1
    db.commit()
    db.refresh(issue)
    return issue

# -----------------------------
# COMMENTS
# -----------------------------

def add_comment(db: Session, issue_id: int, author_id: int, body: str):
    if not body.strip():
        raise ValueError("Comment body cannot be empty")
    if not db.query(User).filter(User.id == author_id).first():
        raise ValueError("Author not found")
    if not db.query(Issue).filter(Issue.id == issue_id).first():
        raise ValueError("Issue not found")
    
    comment = Comment(issue_id=issue_id, author_id=author_id, body=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

# -----------------------------
# LABELS
# -----------------------------

def replace_labels(db: Session, issue_id: int, label_names: List[str]):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    try:
        db.execute(issue_labels.delete().where(issue_labels.c.issue_id == issue_id))
        for name in label_names:
            label = db.query(Label).filter(Label.name == name).first()
            if not label:
                label = Label(name=name)
                db.add(label)
                db.flush()
            db.execute(issue_labels.insert().values(issue_id=issue_id, label_id=label.id))
        
        history = IssueHistory(issue_id=issue_id, action="Labels updated")
        db.add(history)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(issue)
    return issue

# -----------------------------
# BULK STATUS UPDATE
# -----------------------------

def bulk_status_update(db: Session, updates: List[Dict]):
    try:
        for item in updates:
            issue = db.query(Issue).filter(Issue.id == item["issue_id"]).with_for_update().first()
            if not issue:
                raise ValueError(f"Issue {item['issue_id']} not found")
            
            if issue.status == IssueStatus.DONE and item["status"] != IssueStatus.DONE:
                raise ValueError(f"Cannot reopen issue {issue.id}")
            
            old_status = issue.status
            new_status = IssueStatus.from_str(item["status"])
            issue.status = new_status
            if new_status == IssueStatus.DONE:
                issue.resolved_at = datetime.utcnow()
            issue.version += 1
            
            history = IssueHistory(issue_id=issue.id, action=f"Bulk status update: {old_status} -> {issue.status}")
            db.add(history)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    return True

# -----------------------------
# CSV IMPORT
# -----------------------------

def import_issues_csv(db: Session, file_contents: str):
    reader = csv.DictReader(StringIO(file_contents))
    success = 0
    failed = 0
    errors = []

    for row in reader:
        try:
            assignee_id = None
            if row.get("assignee_email"):
                user = db.query(User).filter(User.email == row["assignee_email"].strip()).first()
                if not user:
                    raise ValueError(f"Assignee {row['assignee_email']} not found")
                assignee_id = user.id
            
            create_issue(db, row["title"], row.get("description"), assignee_id)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"Row {success + failed}: {str(e)}")
    
    return {"success": success, "failed": failed, "errors": errors}

# -----------------------------
# REPORTS
# -----------------------------

def top_assignees(db: Session, limit: int = 5):
    return (
        db.query(User.name, func.count(Issue.id).label("issue_count"))
        .join(Issue, Issue.assignee_id == User.id)
        .group_by(User.id, User.name)
        .order_by(func.count(Issue.id).desc())
        .limit(limit)
        .all()
    )

def average_resolution_time(db: Session):
    result = (
        db.query(func.avg(func.extract('epoch', Issue.resolved_at - Issue.created_at)/3600))
        .filter(Issue.resolved_at.isnot(None))
        .scalar()
    )
    return result or 0

# -----------------------------
# TIMELINE
# -----------------------------

def get_issue_timeline(db: Session, issue_id: int):
    return db.query(IssueHistory).filter(IssueHistory.issue_id == issue_id).order_by(IssueHistory.timestamp.asc()).all()
