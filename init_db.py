# init_db.py
from database import Base, engine

# Import all models here so SQLAlchemy knows about them
from models.user import User
from models.label import Label, issue_labels
from models.issue import Issue
from models.comment import Comment

# Create all tables
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
