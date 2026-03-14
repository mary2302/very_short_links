import uuid
from datetime import datetime
from typing import Optional
from fastapi_users import schemas
from pydantic import Field, EmailStr


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema для чтения данных пользователя."""
    id: uuid.UUID
    username: str
    email: EmailStr
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema для регистрации пользователя."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserUpdate(schemas.BaseUserUpdate):
    """Schema для обновления данных пользователя."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
