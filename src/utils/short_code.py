"""Утилита для генерации и валидации коротких кодов."""

import secrets
import string
from typing import Optional
from src.config import get_settings

# Буквы и цифры для генерации короткого кода
ALLOWED_CHARS = string.ascii_letters + string.digits


def generate_short_code(length: Optional[int] = None) -> str:
    """
    Генерирует случайный короткий код заданной длины.
    
    Аргументы:
        length: Длина короткого кода. Если не указано, используется значение из настро
        
    Возвращает:
        Сгенерированный короткий код.
    """
    if length is None:
        settings = get_settings()
        length = settings.short_code_length
    
    return ''.join(secrets.choice(ALLOWED_CHARS) for _ in range(length))


def is_valid_short_code(code: str) -> bool:
    """
    Проверяет, что короткий код содержит только разрешенные символы.
    
    Аргументы:
        code: Короткий код для проверки.
        
    Возвращает:
        True, если код валидный, иначе False.
    """
    if not code:
        return False
    
    # Check length (reasonable bounds)
    if len(code) < 3 or len(code) > 100:
        return False
    
    # Check characters
    allowed_set = set(ALLOWED_CHARS + "-_")
    return all(c in allowed_set for c in code)


def generate_unique_short_code(existing_codes: set, max_attempts: int = 100, length: Optional[int] = None) -> str:
    """
    Генерирует уникальный короткий код, который не существует в заданном множестве.
    
    Аргументы:
        existing_codes: Множество существующих кодов для избежания.
        max_attempts: Максимальное количество попыток генерации.
        length: Длина короткого кода.
        
    Возвращает:
        Уникальный короткий код.
        
    Исключения:
        ValueError: Если не удалось сгенерировать уникальный код после max_attempts попыток.
    """
    for _ in range(max_attempts):
        code = generate_short_code(length)
        if code not in existing_codes:
            return code
    
    raise ValueError(f"Unable to generate unique short code after {max_attempts} attempts")
