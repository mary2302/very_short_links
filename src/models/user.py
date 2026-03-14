from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from src.database import Base


def utc_now():
    """Возвращает текущее время в UTC."""
    return datetime.now(timezone.utc)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User модель для хранения информации о пользователях."""
    
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Связь с Link моделью, каскадное удаление при удалении пользователя
    links = relationship("Link", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

