from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения или .env файла."""
    
    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Настройки для создания и управления сссылками
    default_link_expiry_days: int = 30
    short_code_length: int = 6
    unused_link_cleanup_days: int = 90
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Функция для получения настроек приложения из кэша для оптимизации производительности."""
    return Settings()
