"""User model for authentication with FastAPI Users."""

import uuid
from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from src.database import Base


def utc_now():
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationship with links
    links = relationship("Link", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

