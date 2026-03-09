"""Unit tests for authentication service (FastAPI Users)."""

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
    """Tests for JWT strategy configuration."""
    
    def test_jwt_strategy_creation(self):
        """Test that JWT strategy is created correctly."""
        strategy = get_jwt_strategy()
        
        assert strategy is not None
        assert strategy.lifetime_seconds == settings.access_token_expire_minutes * 60
    
    def test_jwt_strategy_uses_secret(self):
        """Test that JWT strategy uses the configured secret."""
        strategy = get_jwt_strategy()
        
        # The strategy should use our configured secret
        assert hasattr(strategy, 'secret')


class TestUserManager:
    """Tests for UserManager class."""
    
    def test_user_manager_secrets(self):
        """Test that UserManager has correct token secrets."""
        assert UserManager.reset_password_token_secret == settings.secret_key
        assert UserManager.verification_token_secret == settings.secret_key
    
    @pytest.mark.asyncio
    async def test_on_after_register_logs(self, caplog):
        """Test that registration callback logs user ID."""
        caplog.set_level(logging.INFO)
        
        mock_user_db = MagicMock()
        manager = UserManager(mock_user_db)
        
        # Create mock user
        mock_user = MagicMock()
        mock_user.id = "test-uuid-123"
        
        await manager.on_after_register(mock_user)
        
        assert "test-uuid-123" in caplog.text
        assert "registered" in caplog.text


class TestAuthConfiguration:
    """Tests for authentication configuration."""
    
    def test_settings_has_secret_key(self):
        """Test that settings has secret key configured."""
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0
    
    def test_settings_has_algorithm(self):
        """Test that settings has algorithm configured."""
        assert settings.algorithm is not None
        assert settings.algorithm == "HS256"
    
    def test_access_token_expire_minutes(self):
        """Test that access token expiration is configured."""
        assert settings.access_token_expire_minutes > 0
