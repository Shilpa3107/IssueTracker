from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base
from .label import issue_labels

class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

    @classmethod
    def from_str(cls, value: str):
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {value}. Must be OPEN, IN_PROGRESS, or DONE")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    assignee = relationship("User", back_populates="issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete")
    labels = relationship("Label", secondary=issue_labels, back_populates="issues")
    history = relationship("IssueHistory", back_populates="issue", cascade="all, delete")

class IssueHistory(Base):
    __tablename__ = "issue_history"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"))
    action = Column(String(100), nullable=False)  # e.g., "Created", "Status changed to DONE"
    timestamp = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="history")
