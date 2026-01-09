from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Association table for many-to-many
issue_labels = Table(
    "issue_labels",
    Base.metadata,
    Column("issue_id", Integer, ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True 
)

class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # relationships
    issues = relationship("Issue", secondary=issue_labels, back_populates="labels")
