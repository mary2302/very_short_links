import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi_users.password import PasswordHelper

from src.database import Base, get_db
from src.main import app
from src.services.cache_service import CacheService, get_cache_service
from src.services.auth_service import fastapi_users, auth_backend
from src.models.user import User
from src.models.link import Link

# Инициализация PasswordHelper для хеширования паролей в тестах
password_helper = PasswordHelper()


# Тестовая база данных для использования в тестах
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создает и возвращает новый цикл событий для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создает асинхронный движок для тестовой базы данных и управляет созданием/удалением таблиц."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Создает асинхронную сессию для тестовой базы данных."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def mock_cache() -> CacheService:
    """Создает мок сервис кэша."""
    cache = MagicMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=1)
    cache.exists = AsyncMock(return_value=False)
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock(return_value=True)
    cache.get_link = AsyncMock(return_value=None)
    cache.set_link = AsyncMock(return_value=True)
    cache.delete_link = AsyncMock(return_value=1)
    cache.increment_click_count = AsyncMock(return_value=1)
    cache.get_click_count = AsyncMock(return_value=0)
    cache.connect = AsyncMock()
    cache.disconnect = AsyncMock()
    return cache


@pytest_asyncio.fixture(scope="function")
async def client(test_db, mock_cache) -> AsyncGenerator[AsyncClient, None]:
    """Создает асинхронного клиента для тестирования FastAPI приложения 
    с переопределенными зависимостями базы данных и кэша."""
    
    async def override_get_db():
        yield test_db
    
    async def override_get_cache():
        return mock_cache
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache_service] = override_get_cache
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db) -> User:
    """Создает тестового пользователя в базе данных."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=password_helper.hash("testpassword123"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_token(client, test_user) -> str:
    """Получает JWT токен для тестового пользователя."""
    response = await client.post(
        "/auth/jwt/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    return response.json().get("access_token", "")


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user_token) -> dict:
    """Создает заголовки авторизации для аутентифицированных запросов."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture(scope="function")
async def test_link(test_db, test_user) -> Link:
    """Создает тестовую ссылку."""
    link = Link(
        original_url="https://example.com/long-url",
        short_code="abc123",
        owner_id=test_user.id,
        is_active=True,
    )
    test_db.add(link)
    await test_db.commit()
    await test_db.refresh(link)
    return link


@pytest_asyncio.fixture(scope="function")
async def test_link_with_alias(test_db, test_user) -> Link:
    """Создает тестовую ссылку с пользовательским псевдонимом."""
    link = Link(
        original_url="https://example.com/another-url",
        short_code="xyz789",
        custom_alias="my-custom-alias",
        owner_id=test_user.id,
        is_active=True,
    )
    test_db.add(link)
    await test_db.commit()
    await test_db.refresh(link)
    return link


@pytest_asyncio.fixture(scope="function")
async def expired_link(test_db, test_user) -> Link:
    """Создает истекающую тестовую ссылку."""
    link = Link(
        original_url="https://example.com/expired",
        short_code="exp123",
        owner_id=test_user.id,
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    test_db.add(link)
    await test_db.commit()
    await test_db.refresh(link)
    return link


@pytest_asyncio.fixture(scope="function")
async def anonymous_link(test_db) -> Link:
    """Создает анонимную тестовую ссылку (без владельца)."""
    link = Link(
        original_url="https://example.com/anonymous",
        short_code="anon12",
        is_active=True,
    )
    test_db.add(link)
    await test_db.commit()
    await test_db.refresh(link)
    return link
