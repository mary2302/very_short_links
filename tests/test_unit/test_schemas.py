"""Unit tests for Pydantic schemas."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.schemas.link import LinkCreate, LinkUpdate, LinkResponse
from src.schemas.user import UserCreate, UserLogin


class TestLinkCreate:
    """Tests for LinkCreate schema."""
    
    def test_valid_url(self):
        """Test valid URL creation."""
        link = LinkCreate(original_url="https://example.com/page")
        assert link.original_url == "https://example.com/page"
    
    def test_http_url(self):
        """Test HTTP URL is valid."""
        link = LinkCreate(original_url="http://example.com")
        assert link.original_url == "http://example.com"
    
    def test_invalid_url_no_protocol(self):
        """Test URL without protocol is invalid."""
        with pytest.raises(ValidationError):
            LinkCreate(original_url="example.com")
    
    def test_invalid_url_wrong_protocol(self):
        """Test URL with wrong protocol is invalid."""
        with pytest.raises(ValidationError):
            LinkCreate(original_url="ftp://example.com")
    
    def test_valid_custom_alias(self):
        """Test valid custom alias."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="my-custom-link"
        )
        assert link.custom_alias == "my-custom-link"
    
    def test_custom_alias_with_numbers(self):
        """Test custom alias with numbers."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="link123"
        )
        assert link.custom_alias == "link123"
    
    def test_custom_alias_with_underscore(self):
        """Test custom alias with underscore."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="my_link"
        )
        assert link.custom_alias == "my_link"
    
    def test_invalid_custom_alias_special_chars(self):
        """Test custom alias with special characters is invalid."""
        with pytest.raises(ValidationError):
            LinkCreate(
                original_url="https://example.com",
                custom_alias="my@link"
            )
    
    def test_custom_alias_too_short(self):
        """Test custom alias too short."""
        with pytest.raises(ValidationError):
            LinkCreate(
                original_url="https://example.com",
                custom_alias="ab"
            )
    
    def test_valid_expires_at(self):
        """Test valid expiration datetime."""
        future_date = datetime.utcnow() + timedelta(days=7)
        link = LinkCreate(
            original_url="https://example.com",
            expires_at=future_date
        )
        assert link.expires_at == future_date
    
    def test_project_field(self):
        """Test project field."""
        link = LinkCreate(
            original_url="https://example.com",
            project="my-project"
        )
        assert link.project == "my-project"


class TestLinkUpdate:
    """Tests for LinkUpdate schema."""
    
    def test_partial_update_url(self):
        """Test partial update with only URL."""
        update = LinkUpdate(original_url="https://newurl.com")
        assert update.original_url == "https://newurl.com"
        assert update.custom_alias is None
    
    def test_partial_update_alias(self):
        """Test partial update with only alias."""
        update = LinkUpdate(custom_alias="new-alias")
        assert update.custom_alias == "new-alias"
        assert update.original_url is None
    
    def test_all_fields_none(self):
        """Test update with all fields None."""
        update = LinkUpdate()
        assert update.original_url is None
        assert update.custom_alias is None
        assert update.expires_at is None


class TestUserCreate:
    """Tests for UserCreate schema."""
    
    def test_valid_user(self):
        """Test valid user creation."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
    
    def test_invalid_email(self):
        """Test invalid email format."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="password123"
            )
    
    def test_username_too_short(self):
        """Test username too short."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="password123"
            )
    
    def test_password_too_short(self):
        """Test password too short."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="12345"
            )


class TestUserLogin:
    """Tests for UserLogin schema."""
    
    def test_valid_login(self):
        """Test valid login data."""
        login = UserLogin(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"
