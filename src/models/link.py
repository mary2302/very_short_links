"""Link model for URL shortening."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Uuid
from sqlalchemy.orm import relationship
from src.database import Base


def utc_now():
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class Link(Base):
    """Link model for storing shortened URLs."""
    
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String(2048), nullable=False, index=True)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    custom_alias = Column(String(100), unique=True, nullable=True, index=True)
    
    # Statistics
    click_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Owner relationship (nullable for anonymous users)
    owner_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")
    
    # Project grouping (optional feature)
    project = Column(String(100), nullable=True, index=True)
    
    def __repr__(self):
        return f"<Link(id={self.id}, short_code={self.short_code}, original_url={self.original_url[:50]}...)>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the link has expired."""
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        # Handle both naive and aware datetimes
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires
    
    @property
    def effective_short_code(self) -> str:
        """Return custom alias if set, otherwise short_code."""
        return self.custom_alias or self.short_code
