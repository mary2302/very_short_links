import pytest
from unittest.mock import MagicMock
import logging

from src.services.auth_service import (
    get_jwt_strategy,
    UserManager,
)
from src.config import get_settings

settings = get_settings()


class TestJWTStrategy:
    """Тесты для JWT стратегии аутентификации."""
    
    def test_jwt_strategy_creation(self):
        """Тест создания JWT стратегии."""
        strategy = get_jwt_strategy()
        
        assert strategy is not None
        assert strategy.lifetime_seconds == settings.access_token_expire_minutes * 60
    
    def test_jwt_strategy_uses_secret(self):
        """Тест того, что JWT стратегия использует сконфигурированный секрет."""
        strategy = get_jwt_strategy()
        
        assert hasattr(strategy, 'secret')


class TestUserManager:
    """Тесты для UserManager класса"""
    
    def test_user_manager_secrets(self):
        """Тест того, что UserManager имеет правильные секреты токенов."""
        assert UserManager.reset_password_token_secret == settings.secret_key
        assert UserManager.verification_token_secret == settings.secret_key
    
    @pytest.mark.asyncio
    async def test_on_after_register_logs(self, caplog):
        """Тест того, что обратный вызов регистрации логирует ID пользователя."""
        caplog.set_level(logging.INFO)
        
        mock_user_db = MagicMock()
        manager = UserManager(mock_user_db)
        
        # Создаем мок пользователя
        mock_user = MagicMock()
        mock_user.id = "test-uuid-123"
        
        await manager.on_after_register(mock_user)
        
        assert "test-uuid-123" in caplog.text
        assert "registered" in caplog.text


class TestAuthConfiguration:
    """Тесты аутентификации."""
    
    def test_settings_has_secret_key(self):
        """Тест того, что в настройках есть секретный ключ для JWT."""
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0
    
    def test_settings_has_algorithm(self):
        """Тест того, что настройки содержат сконфигурированный алгоритм."""
        assert settings.algorithm is not None
        assert settings.algorithm == "HS256"
    
    def test_access_token_expire_minutes(self):
        """Тест того, что истечение срока действия токена доступа установлено."""
        assert settings.access_token_expire_minutes > 0
