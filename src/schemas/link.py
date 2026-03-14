import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator


class LinkBase(BaseModel):
    """Базовая схема для ссылки."""
    original_url: str = Field(..., max_length=2048)
    
    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Проверяет, что URL правильно отформатирован."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkCreate(LinkBase):
    """Schema для создания новой ссылки."""
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=100)
    expires_at: Optional[datetime] = None
    project: Optional[str] = Field(None, max_length=100)
    
    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, v: Optional[str]) -> Optional[str]:
        """валидирует, что custom_alias содержит только разрешенные символы."""
        if v is None:
            return v
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Custom alias can only contain letters, numbers, hyphens and underscores")
        return v


class LinkUpdate(BaseModel):
    """Schema для обновления существующей ссылки."""
    original_url: Optional[str] = Field(None, max_length=2048)
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=100)
    expires_at: Optional[datetime] = None
    project: Optional[str] = Field(None, max_length=100)
    
    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """валидирует, что URL начинается с http:// или https://"""
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkResponse(BaseModel):
    """Schema для ответа"""
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str] = None
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    project: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    
    class Config:
        from_attributes = True


class LinkStats(BaseModel):
    """Schema ддля статистики ссылки."""
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str] = None
    click_count: int
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    project: Optional[str] = None
    
    class Config:
        from_attributes = True


class LinkSearchResult(BaseModel):
    """Schema для результатов поиска ссылок."""
    links: List[LinkResponse]
    total: int


class ExpiredLinkInfo(BaseModel):
    """Schema для информации об истекших ссылках."""
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str] = None
    click_count: int
    created_at: datetime
    expired_at: datetime
    
    class Config:
        from_attributes = True
