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
    """Получает экземпляр SQLAlchemyUserDatabase для работы с пользователями в базе данных."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager для управления операциями с пользователями (регистрация, аутентификация и т.д.)"""
    
    # Секретные ключи для генерации токенов сброса пароля и верификации
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def validate_password(self, password: str, user: schemas.UC) -> None:
        """Проверяет валидность пароля при регистрации или смене пароля.
        В данном случае, просто проверяем минимальную длину пароля."""
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password too short")

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Callback после успешной регистрации пользователя, логирует информацию о новом пользователе."""
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        """Callback после запроса на сброс пароля, логирует информацию о пользователе и токене сброса пароля."""
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        """Callback после запроса на верификацию email, логирует информацию о пользователе и токене верификации."""
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")
    
    async def create(
        self,
        user_create: schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """Переопределение метода create для добавления проверки на уникальность имени пользователя при регистрации нового пользователя."""
        # Check for duplicate username
        existing_user = await self.user_db.session.execute(
            select(User).where(User.username == user_create.username)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        return await super().create(user_create, safe, request)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Получает экземпляр UserManager для управления пользователями, используя SQLAlchemyUserDatabase в качестве источника данных."""
    yield UserManager(user_db)


# Bearer transport для JWT tokens - используется для передачи токенов в заголовке Authorization
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """Стратегия JWT для аутентификации, использует секретный ключ и время жизни токена из настроек."""
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

# FastAPI Users инстанс для управления пользователями и аутентификацией, использующий UserManager и JWT authentication backend
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Декоратор для получения текущего активного пользователя, который требует аутентификации и проверяет, что пользователь активен
current_active_user = fastapi_users.current_user(active=True)

# Для поддержки как аутентифицированных, так и неаутентифицированных пользователей в некоторых эндпоинтах, можно использовать current_user с optional=True
current_user_optional = fastapi_users.current_user(active=True, optional=True)
