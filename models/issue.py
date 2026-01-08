from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    version = Column(Integer, default=1)  # for concurrency control
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # relationships
    assignee = relationship("User", back_populates="issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete")
    labels = relationship("Label", secondary="issue_labels", back_populates="issues")
