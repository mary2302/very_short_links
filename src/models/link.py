"""Link модель для хранения сокращенных URL."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Uuid
from sqlalchemy.orm import relationship
from src.database import Base


def utc_now():
    """Возвращает текущее время в UTC."""
    return datetime.now(timezone.utc)


class Link(Base):
    """Link модель для хранения сокращенных URL."""
    
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String(2048), nullable=False, index=True)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    custom_alias = Column(String(100), unique=True, nullable=True, index=True)
    
    # Статистика доступа
    click_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Статус активности
    is_active = Column(Boolean, default=True)
    
    # Связь с владельцем (nullable для анонимных пользователей)
    owner_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")
    
    # Группировка по проектам
    project = Column(String(100), nullable=True, index=True)
    
    # Представление для отладки
    def __repr__(self):
        return f"<Link(id={self.id}, short_code={self.short_code}, original_url={self.original_url[:50]}...)>"
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия ссылки. Если expires_at не установлен, ссылка не считается истекшей."""
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        # Если expires_at не содержит информацию о часовом поясе, считаем его в UTC
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires
    
    @property
    def effective_short_code(self) -> str:
        """Возвращает пользовательский псевдоним, если он его установил, иначе короткий код."""
        return self.custom_alias or self.short_code
