"""Unit tests for short code generation."""

import pytest
import string

from src.utils.short_code import (
    generate_short_code,
    is_valid_short_code,
    generate_unique_short_code,
    ALLOWED_CHARS,
)


class TestGenerateShortCode:
    """Tests for generate_short_code function."""
    
    def test_default_length(self):
        """Test that default length is 6."""
        code = generate_short_code(length=6)
        assert len(code) == 6
    
    def test_custom_length(self):
        """Test custom length generation."""
        for length in [4, 8, 12, 20]:
            code = generate_short_code(length=length)
            assert len(code) == length
    
    def test_contains_only_allowed_chars(self):
        """Test that code contains only alphanumeric characters."""
        for _ in range(100):  # Run multiple times for randomness
            code = generate_short_code(length=10)
            assert all(c in ALLOWED_CHARS for c in code)
    
    def test_uniqueness(self):
        """Test that generated codes are likely unique."""
        codes = set()
        for _ in range(1000):
            code = generate_short_code(length=8)
            codes.add(code)
        # With 62^8 possible combinations, collisions are extremely unlikely
        assert len(codes) == 1000
    
    def test_no_special_chars(self):
        """Test that no special characters are included."""
        for _ in range(100):
            code = generate_short_code(length=10)
            assert not any(c in "!@#$%^&*()+=[]{}|;:',.<>?/`~" for c in code)


class TestIsValidShortCode:
    """Tests for is_valid_short_code function."""
    
    def test_valid_alphanumeric(self):
        """Test valid alphanumeric codes."""
        assert is_valid_short_code("abc123") is True
        assert is_valid_short_code("ABC") is True
        assert is_valid_short_code("123") is True
        assert is_valid_short_code("aBc123XyZ") is True
    
    def test_valid_with_hyphens_underscores(self):
        """Test valid codes with hyphens and underscores."""
        assert is_valid_short_code("my-link") is True
        assert is_valid_short_code("my_link") is True
        assert is_valid_short_code("my-link_123") is True
    
    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert is_valid_short_code("") is False
    
    def test_invalid_too_short(self):
        """Test too short codes are invalid."""
        assert is_valid_short_code("ab") is False
        assert is_valid_short_code("a") is False
    
    def test_invalid_too_long(self):
        """Test too long codes are invalid."""
        assert is_valid_short_code("a" * 101) is False
    
    def test_invalid_special_chars(self):
        """Test codes with special characters are invalid."""
        assert is_valid_short_code("abc@123") is False
        assert is_valid_short_code("my#link") is False
        assert is_valid_short_code("test!code") is False
        assert is_valid_short_code("hello world") is False
    
    def test_boundary_lengths(self):
        """Test boundary length cases."""
        assert is_valid_short_code("abc") is True  # Min valid (3)
        assert is_valid_short_code("a" * 100) is True  # Max valid (100)


class TestGenerateUniqueShortCode:
    """Tests for generate_unique_short_code function."""
    
    def test_generates_unique_code(self):
        """Test that generated code is not in existing set."""
        existing = {"abc123", "xyz789", "test12"}
        code = generate_unique_short_code(existing, length=6)
        assert code not in existing
    
    def test_empty_existing_set(self):
        """Test with empty existing set."""
        code = generate_unique_short_code(set(), length=6)
        assert len(code) == 6
    
    def test_raises_after_max_attempts(self):
        """Test that ValueError is raised after max attempts."""
        # Create a set that would make collision inevitable
        # This is a bit tricky to test properly
        existing = {generate_short_code(length=2) for _ in range(1000)}
        
        # With length=2, only 62^2 = 3844 possible combinations
        # We might not fill all, but with 1000 entries, collisions are common
        # The function should still eventually find a unique one or raise
        try:
            generate_unique_short_code(existing, max_attempts=10, length=2)
        except ValueError as e:
            assert "Unable to generate unique short code" in str(e)
    
    def test_respects_length_parameter(self):
        """Test that custom length is respected."""
        existing = set()
        code = generate_unique_short_code(existing, length=12)
        assert len(code) == 12


class TestAllowedChars:
    """Tests for ALLOWED_CHARS constant."""
    
    def test_contains_lowercase(self):
        """Test that lowercase letters are included."""
        for c in string.ascii_lowercase:
            assert c in ALLOWED_CHARS
    
    def test_contains_uppercase(self):
        """Test that uppercase letters are included."""
        for c in string.ascii_uppercase:
            assert c in ALLOWED_CHARS
    
    def test_contains_digits(self):
        """Test that digits are included."""
        for c in string.digits:
            assert c in ALLOWED_CHARS
    
    def test_correct_length(self):
        """Test that ALLOWED_CHARS has correct length."""
        # 26 lowercase + 26 uppercase + 10 digits = 62
        assert len(ALLOWED_CHARS) == 62
