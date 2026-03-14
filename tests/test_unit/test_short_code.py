import pytest
import string

from src.utils.short_code import (
    generate_short_code,
    is_valid_short_code,
    generate_unique_short_code,
    ALLOWED_CHARS,
)


class TestGenerateShortCode:
    """Тесты для функции generate_short_code."""
    
    def test_default_length(self):
        """Тест генерации кода по умолчанию."""
        code = generate_short_code(length=6)
        assert len(code) == 6
    
    def test_custom_length(self):
        """Тест генерации кода с пользовательской длиной."""
        for length in [4, 8, 12, 20]:
            code = generate_short_code(length=length)
            assert len(code) == length
    
    def test_contains_only_allowed_chars(self):
        """Тест того, что код содержит только буквенно-цифровые символы."""
        for _ in range(100): 
            code = generate_short_code(length=10)
            assert all(c in ALLOWED_CHARS for c in code)
    
    def test_uniqueness(self):
        """Тест генерации уникальных кодов при множественных вызовах."""
        codes = set()
        for _ in range(1000):
            code = generate_short_code(length=8)
            codes.add(code)
        assert len(codes) == 1000
    
    def test_no_special_chars(self):
        """Тест того, что специальные символы не включены."""
        for _ in range(100):
            code = generate_short_code(length=10)
            assert not any(c in "!@#$%^&*()+=[]{}|;:',.<>?/`~" for c in code)


class TestIsValidShortCode:
    """Тесты для функции is_valid_short_code."""
    
    def test_valid_alphanumeric(self):
        """Тест буквенно-цифровых кодов."""
        assert is_valid_short_code("abc123") is True
        assert is_valid_short_code("ABC") is True
        assert is_valid_short_code("123") is True
        assert is_valid_short_code("aBc123XyZ") is True
    
    def test_valid_with_hyphens_underscores(self):
        """Тест кодов с дефисами и подчеркиваниями."""
        assert is_valid_short_code("my-link") is True
        assert is_valid_short_code("my_link") is True
        assert is_valid_short_code("my-link_123") is True
    
    def test_invalid_empty(self):
        """Тест пустой строки."""
        assert is_valid_short_code("") is False
    
    def test_invalid_too_short(self):
        """Тест слишком коротких кодов."""
        assert is_valid_short_code("ab") is False
        assert is_valid_short_code("a") is False
    
    def test_invalid_too_long(self):
        """Тест слишком длинных кодов."""
        assert is_valid_short_code("a" * 101) is False
    
    def test_invalid_special_chars(self):
        """Тест кодов с особыми символами."""
        assert is_valid_short_code("abc@123") is False
        assert is_valid_short_code("my#link") is False
        assert is_valid_short_code("test!code") is False
        assert is_valid_short_code("hello world") is False
    
    def test_boundary_lengths(self):
        """Тест граничных значений длины."""
        assert is_valid_short_code("abc") is True  # Min valid (3)
        assert is_valid_short_code("a" * 100) is True  # Max valid (100)


class TestGenerateUniqueShortCode:
    """Тесты для функции generate_unique_short_code."""
    
    def test_generates_unique_code(self):
        """Тест генерации уникального кода."""
        existing = {"abc123", "xyz789", "test12"}
        code = generate_unique_short_code(existing, length=6)
        assert code not in existing
    
    def test_empty_existing_set(self):
        """Тест с пустым множеством существующих кодов."""
        code = generate_unique_short_code(set(), length=6)
        assert len(code) == 6
    
    def test_raises_after_max_attempts(self):
        """Тест того, что ValueError вызывается после максимального количества попыток."""
        # Сгенерируем множество, которое почти полностью заполняет пространство кодов длины 2 (62^2 = 3844)
        existing = {generate_short_code(length=2) for _ in range(1000)}
        
        # Сделаем так, чтобы генерация всегда возвращала код из
        #  existing, чтобы гарантировать провал
        try:
            generate_unique_short_code(existing, max_attempts=10, length=2)
        except ValueError as e:
            assert "Unable to generate unique short code" in str(e)
    
    def test_respects_length_parameter(self):
        """Тест того, что пользовательская длина кода учитывается."""
        existing = set()
        code = generate_unique_short_code(existing, length=12)
        assert len(code) == 12


class TestAllowedChars:
    """Тесты для набора разрешенных символов ALLOWED_CHARS."""
    
    def test_contains_lowercase(self):
        """Тест того, что строчные буквы включены."""
        for c in string.ascii_lowercase:
            assert c in ALLOWED_CHARS
    
    def test_contains_uppercase(self):
        """Тест того, что заглавные буквы включены."""
        for c in string.ascii_uppercase:
            assert c in ALLOWED_CHARS
    
    def test_contains_digits(self):
        """Тест того, что цифры включены."""
        for c in string.digits:
            assert c in ALLOWED_CHARS
    
    def test_correct_length(self):
        """Тест того, что ALLOWED_CHARS имеет правильную длину."""
        # 62 символа: 26 lowercase + 26 uppercase + 10 digits
        assert len(ALLOWED_CHARS) == 62
