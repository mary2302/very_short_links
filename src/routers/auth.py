from fastapi import APIRouter
from src.schemas.user import UserCreate, UserRead, UserUpdate
from src.services.auth_service import auth_backend, fastapi_users

router = APIRouter()
router.include_router(
    fastapi_users.get_auth_router(auth_backend), # для аутентификации (логин, logout, refresh)
    prefix="/auth/jwt",
    tags=["Authentication"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), # Регистрация пользователей
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    fastapi_users.get_reset_password_router(), # Сброс пароля
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead), # Подтверждение email
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate), # Управление пользователями
    prefix="/users",
    tags=["Users"],
)
