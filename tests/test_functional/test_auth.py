import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    """Тесты регистрации пользователей."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Тест регистрации с уже существующим именем пользователя."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",
                "password": "password123"
            }
        )
        
        # FastAPI Users возвращает 400 при дублирующемся имени пользователя
        assert response.status_code == 400
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Тест регистрации с уже существующим email."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "username": "differentuser",
                "password": "password123"
            }
        )
        
        # FastAPI Users возвращает 400 при дублирующемся email
        assert response.status_code == 400
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Тест регистрации с недействительным email."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "not_valid_email",
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_register_short_password(self, client: AsyncClient):
        """Тест регистрации с слишком коротким паролем."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "12345"
            }
        )
        
        assert response.status_code == 422
    
    async def test_register_short_username(self, client: AsyncClient):
        """Тест регистрации с слишком коротким именем пользователя."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Тесты входа пользователя."""
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Тест успешного входа."""
        response = await client.post(
            "/auth/jwt/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Тест входа с неправильным паролем."""
        response = await client.post(
            "/auth/jwt/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 400
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Тест входа с несуществующим пользователем."""
        response = await client.post(
            "/auth/jwt/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
    
    async def test_login_missing_fields(self, client: AsyncClient):
        """Тест входа с отсутствующими полями."""
        response = await client.post(
            "/auth/jwt/login",
            data={}
        )
        
        assert response.status_code == 422
