"""Authentication service using FastAPI Users."""

import uuid
import logging
from typing import Optional

from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config import get_settings
from src.database import get_db
from src.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


async def get_user_db(session: AsyncSession = Depends(get_db)):
    """Get SQLAlchemy user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager for handling user-related operations."""
    
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def validate_password(
        self, password: str, user: schemas.UC
    ) -> None:
        """Validate password on registration."""
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password too short")

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Callback after user registration."""
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Callback after forgot password request."""
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Callback after verification request."""
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")
    
    async def create(
        self,
        user_create: schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """Create a user, checking for duplicate username."""
        # Check for duplicate username
        existing_user = await self.user_db.session.execute(
            select(User).where(User.username == user_create.username)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        return await super().create(user_create, safe, request)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get user manager instance."""
    yield UserManager(user_db)


# Bearer transport for JWT tokens
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication."""
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_minutes * 60
    )


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Current active user dependency
current_active_user = fastapi_users.current_user(active=True)

# Optional current user (for endpoints that work both with and without auth)
current_user_optional = fastapi_users.current_user(active=True, optional=True)
