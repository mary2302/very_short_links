"""Link schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator


class LinkBase(BaseModel):
    """Base link schema."""
    original_url: str = Field(..., max_length=2048)
    
    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkCreate(LinkBase):
    """Schema for creating a new link."""
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=100)
    expires_at: Optional[datetime] = None
    project: Optional[str] = Field(None, max_length=100)
    
    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, v: Optional[str]) -> Optional[str]:
        """Validate custom alias contains only allowed characters."""
        if v is None:
            return v
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Custom alias can only contain letters, numbers, hyphens and underscores")
        return v


class LinkUpdate(BaseModel):
    """Schema for updating a link."""
    original_url: Optional[str] = Field(None, max_length=2048)
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=100)
    expires_at: Optional[datetime] = None
    project: Optional[str] = Field(None, max_length=100)
    
    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the URL is properly formatted."""
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkResponse(BaseModel):
    """Schema for link response."""
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
    """Schema for link statistics."""
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
    """Schema for link search results."""
    links: List[LinkResponse]
    total: int


class ExpiredLinkInfo(BaseModel):
    """Schema for expired link information."""
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str] = None
    click_count: int
    created_at: datetime
    expired_at: datetime
    
    class Config:
        from_attributes = True
