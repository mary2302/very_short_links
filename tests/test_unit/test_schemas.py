import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.schemas.link import LinkCreate, LinkUpdate
from src.schemas.user import UserCreate


class TestLinkCreate:
    """Тесты для схемы LinkCreate."""
    
    def test_valid_url(self):
        """Тест валидного URL."""
        link = LinkCreate(original_url="https://example.com/page")
        assert link.original_url == "https://example.com/page"
    
    def test_http_url(self):
        """Тест HTTP URL."""
        link = LinkCreate(original_url="http://example.com")
        assert link.original_url == "http://example.com"
    
    def test_invalid_url_no_protocol(self):
        """Тест URL без протокола."""
        with pytest.raises(ValidationError):
            LinkCreate(original_url="example.com")
    
    def test_invalid_url_wrong_protocol(self):
        """Тест URL с неправильным протоколом."""
        with pytest.raises(ValidationError):
            LinkCreate(original_url="ftp://example.com")
    
    def test_valid_custom_alias(self):
        """Тест валидного пользовательского псевдонима."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="my-custom-link"
        )
        assert link.custom_alias == "my-custom-link"
    
    def test_custom_alias_with_numbers(self):
        """Тест пользовательского псевдонима с числами."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="link123"
        )
        assert link.custom_alias == "link123"
    
    def test_custom_alias_with_underscore(self):
        """Тест пользовательского псевдонима с подчеркиванием."""
        link = LinkCreate(
            original_url="https://example.com",
            custom_alias="my_link"
        )
        assert link.custom_alias == "my_link"
    
    def test_invalid_custom_alias_special_chars(self):
        """Тест пользовательского псевдонима с особыми символами."""
        with pytest.raises(ValidationError):
            LinkCreate(
                original_url="https://example.com",
                custom_alias="my@link"
            )
    
    def test_custom_alias_too_short(self):
        """Тест пользовательского псевдонима, который слишком короткий."""
        with pytest.raises(ValidationError):
            LinkCreate(
                original_url="https://example.com",
                custom_alias="ab"
            )
    
    def test_valid_expires_at(self):
        """Тест валидной даты истечения."""
        future_date = datetime.utcnow() + timedelta(days=7)
        link = LinkCreate(
            original_url="https://example.com",
            expires_at=future_date
        )
        assert link.expires_at == future_date
    
    def test_project_field(self):
        """Тест поля проекта."""
        link = LinkCreate(
            original_url="https://example.com",
            project="my-project"
        )
        assert link.project == "my-project"


class TestLinkUpdate:
    """Тесты для схемы LinkUpdate."""
    
    def test_partial_update_url(self):
        """Тест частичного обновления с только URL."""
        update = LinkUpdate(original_url="https://newurl.com")
        assert update.original_url == "https://newurl.com"
        assert update.custom_alias is None
    
    def test_partial_update_alias(self):
        """Тест частичного обновления с только псевдонимом."""
        update = LinkUpdate(custom_alias="new-alias")
        assert update.custom_alias == "new-alias"
        assert update.original_url is None
    
    def test_all_fields_none(self):
        """Тест частичного обновления со всеми полями None."""
        update = LinkUpdate()
        assert update.original_url is None
        assert update.custom_alias is None
        assert update.expires_at is None


class TestUserCreate:
    """Тесты для схемы UserCreate."""
    
    def test_valid_user(self):
        """Тест валидного создания пользователя."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
    
    def test_invalid_email(self):
        """Тест недействительного формата email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not_an_email",  # No @ symbol
                username="testuser",
                password="password123"
            )
    
    def test_username_too_short(self):
        """Тест username слишком короткий."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="password123"
            )
    
    def test_password_too_short(self):
        """Тест password слишком короткий."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="12345"
            )



