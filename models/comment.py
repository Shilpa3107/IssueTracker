from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    body = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")
