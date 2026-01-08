from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.issue import Issue, IssueStatus
from models.user import User
from models.label import Label, issue_labels
from models.comment import Comment
from typing import List, Dict
from datetime import datetime
import csv
from io import StringIO

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
    db.commit()
    db.refresh(issue)
    return issue

def update_issue(db: Session, issue_id: int, data: dict):
    # data must include version
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    if data.get("version") != issue.version:
        raise ValueError("Version conflict")

    # Update fields
    for key in ["title", "description", "status", "assignee_id"]:
        if key in data and data[key] is not None:
            setattr(issue, key, data[key])
    
    # Update resolved_at if status DONE
    if data.get("status") == IssueStatus.DONE:
        issue.resolved_at = datetime.utcnow()
    
    issue.version += 1  # increment version
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
    from models.issue import issue_labels  # association table

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    # Start transaction
    try:
        # Delete existing labels
        db.execute(issue_labels.delete().where(issue_labels.c.issue_id == issue_id))
        
        # Add new labels
        for name in label_names:
            label = db.query(Label).filter(Label.name == name).first()
            if not label:
                label = Label(name=name)
                db.add(label)
                db.flush()  # get id without commit
            db.execute(issue_labels.insert().values(issue_id=issue_id, label_id=label.id))
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
    """
    updates = [{"issue_id": 1, "status": "DONE"}, ...]
    Rollback if any update fails
    """
    try:
        for item in updates:
            issue = db.query(Issue).filter(Issue.id == item["issue_id"]).first()
            if not issue:
                raise ValueError(f"Issue {item['issue_id']} not found")
            # Example rule: can't reopen a DONE issue
            if issue.status == IssueStatus.DONE and item["status"] != IssueStatus.DONE:
                raise ValueError(f"Cannot reopen issue {issue.id}")
            issue.status = item["status"]
            if item["status"] == IssueStatus.DONE:
                issue.resolved_at = datetime.utcnow()
            issue.version += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    return True

# -----------------------------
# CSV IMPORT
# -----------------------------

def import_issues_csv(db: Session, file_contents: str):
    """
    file_contents: CSV string with headers: title,description,assignee_email
    Returns summary: {"success": int, "failed": int, "errors": [list]}
    """
    reader = csv.DictReader(StringIO(file_contents))
    success = 0
    failed = 0
    errors = []

    for row in reader:
        try:
            assignee_id = None
            if row.get("assignee_email"):
                user = db.query(User).filter(User.email == row["assignee_email"]).first()
                if not user:
                    raise ValueError(f"Assignee {row['assignee_email']} not found")
                assignee_id = user.id
            create_issue(db, title=row["title"], description=row.get("description"), assignee_id=assignee_id)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(str(e))
    return {"success": success, "failed": failed, "errors": errors}

# -----------------------------
# REPORTS
# -----------------------------

def top_assignees(db: Session, limit: int = 5):
    """
    Returns top assignees by number of issues assigned
    """
    from sqlalchemy import func
    return (
        db.query(User.name, func.count(Issue.id).label("issue_count"))
        .join(Issue, Issue.assignee_id == User.id)
        .group_by(User.id)
        .order_by(func.count(Issue.id).desc())
        .limit(limit)
        .all()
    )

def average_resolution_time(db: Session):
    """
    Returns average time in hours for resolved issues
    """
    from sqlalchemy import func
    result = (
        db.query(func.avg(func.extract('epoch', Issue.resolved_at - Issue.created_at)/3600))
        .filter(Issue.resolved_at.isnot(None))
        .scalar()
    )
    return result or 0

def update_issue(db: Session, issue_id: int, data: dict):
    issue = db.query(Issue).filter(Issue.id == issue_id).with_for_update().first()  # lock row
    if not issue:
        raise ValueError("Issue not found")

    # Check version for optimistic concurrency
    if data.get("version") != issue.version:
        raise ValueError("Version conflict")

    # Apply updates
    for key in ["title", "description", "status", "assignee_id"]:
        if key in data and data[key] is not None:
            setattr(issue, key, data[key])

    if data.get("status") == IssueStatus.DONE:
        issue.resolved_at = datetime.utcnow()

    issue.version += 1  # increment version

    db.commit()
    db.refresh(issue)
    return issue

def replace_labels(db: Session, issue_id: int, label_names: List[str]):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    # Start a transaction for atomicity
    try:
        with db.begin():  # transaction starts here
            # Remove existing labels
            db.execute(issue_labels.delete().where(issue_labels.c.issue_id == issue_id))

            # Add new labels
            for name in label_names:
                label = db.query(Label).filter(Label.name == name).first()
                if not label:
                    label = Label(name=name)
                    db.add(label)
                    db.flush()  # get ID without commit
                db.execute(issue_labels.insert().values(issue_id=issue_id, label_id=label.id))
    except Exception as e:
        db.rollback()
        raise e

    db.refresh(issue)
    return issue

def bulk_status_update(db: Session, updates: List[Dict]):
    """
    updates = [{"issue_id": 1, "status": "DONE"}, ...]
    Rollback entire batch if any update fails
    """
    try:
        with db.begin():  # start transaction
            for item in updates:
                issue = db.query(Issue).filter(Issue.id == item["issue_id"]).first()
                if not issue:
                    raise ValueError(f"Issue {item['issue_id']} not found")

                # Example rule: can't reopen DONE issue
                if issue.status == IssueStatus.DONE and item["status"] != IssueStatus.DONE:
                    raise ValueError(f"Cannot reopen issue {issue.id}")

                issue.status = item["status"]
                if item["status"] == IssueStatus.DONE:
                    issue.resolved_at = datetime.utcnow()
                issue.version += 1  # increment version
    except Exception as e:
        db.rollback()  # rollback entire transaction
        raise e

    return True

def import_issues_csv(db: Session, file_contents: str):
    from io import StringIO
    import csv

    reader = csv.DictReader(StringIO(file_contents))
    success = 0
    failed = 0
    errors = []

    try:
        with db.begin():  # start transaction
            for row in reader:
                try:
                    assignee_id = None
                    if row.get("assignee_email"):
                        user = db.query(User).filter(User.email == row["assignee_email"]).first()
                        if not user:
                            raise ValueError(f"Assignee {row['assignee_email']} not found")
                        assignee_id = user.id

                    create_issue(db, row["title"], row.get("description"), assignee_id)
                    success += 1
                except Exception as e:
                    failed += 1
                    errors.append(str(e))
                    # continue to next row; transaction still safe
    except Exception as e:
        db.rollback()
        raise e

    return {"success": success, "failed": failed, "errors": errors}
