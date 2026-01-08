from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # relationships
    issues = relationship("Issue", secondary="issue_labels", back_populates="labels")
