"""Unit tests for authentication service."""

import pytest
from datetime import timedelta
from jose import jwt

from src.services.auth_service import AuthService
from src.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "mysecurepassword"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "mysecurepassword"
        wrong_password = "wrongpassword"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = AuthService.get_password_hash("password1")
        hash2 = AuthService.get_password_hash("password2")
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"
        hash1 = AuthService.get_password_hash(password)
        hash2 = AuthService.get_password_hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)


class TestJWTToken:
    """Tests for JWT token creation."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "testuser", "user_id": 1}
        token = AuthService.create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
    
    def test_token_contains_payload(self):
        """Test that token contains correct payload."""
        data = {"sub": "testuser", "user_id": 123}
        token = AuthService.create_access_token(data)
        
        # Decode and verify
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 123
        assert "exp" in payload
    
    def test_token_with_custom_expiry(self):
        """Test token with custom expiration."""
        data = {"sub": "testuser"}
        expires = timedelta(hours=2)
        token = AuthService.create_access_token(data, expires_delta=expires)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert "exp" in payload
    
    def test_token_without_custom_expiry(self):
        """Test token with default expiration."""
        data = {"sub": "testuser"}
        token = AuthService.create_access_token(data)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert "exp" in payload
