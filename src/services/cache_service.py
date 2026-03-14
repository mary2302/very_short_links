import json
import logging
from typing import Optional
import redis.asyncio as redis
from redis.exceptions import RedisError
from src.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для управления кэшированием данных в Redis. 
    Предоставляет методы для получения, 
    установки и удаления данных из кэша, 
    а также специализированные методы для работы 
    с данными ссылок и счетчиками кликов."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        # Подключение к Redis
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            except RedisError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self._redis:
            try:
                await self._redis.close()
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """Получает значение из кэша по ключу. Возвращает None при ошибках Redis."""
        try:
            if self._redis is None:
                await self.connect()
            if self._redis is None:
                return None
            return await self._redis.get(key)
        except RedisError as e:
            logger.warning(f"Redis get error for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Устанавливает значение в кэше с заданным временем жизни. Возвращает False при ошибках Redis."""
        try:
            if self._redis is None:
                await self.connect()
            if self._redis is None:
                return False
            return await self._redis.set(key, value, ex=expire)
        except RedisError as e:
            logger.warning(f"Redis set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> int:
        """Удаляет ключ из кэша. Возвращает 0 при ошибках Redis."""
        try:
            if self._redis is None:
                await self.connect()
            if self._redis is None:
                return 0
            return await self._redis.delete(key)
        except RedisError as e:
            logger.warning(f"Redis delete error for key '{key}': {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Проверяет, существует ли ключ в кэше. Возвращает False при ошибках Redis."""
        try:
            if self._redis is None:
                await self.connect()
            if self._redis is None:
                return False
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Redis exists error for key '{key}': {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Получает JSON значение из кэша."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for key '{key}': {e}")
                return None
        return None
    
    async def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """Устанавливает JSON значение в кэше."""
        return await self.set(key, json.dumps(value), expire)
    
    async def increment(self, key: str) -> int:
        """Инкремент по числовому значению по ключу. Возвращает новое значение или 0 при ошибках Redis."""
        try:
            if self._redis is None:
                await self.connect()
            if self._redis is None:
                return 0
            return await self._redis.incr(key)
        except RedisError as e:
            logger.warning(f"Redis increment error for key '{key}': {e}")
            return 0
    
    async def get_link(self, short_code: str) -> Optional[dict]:
        """Получает кэшированные данные ссылки."""
        return await self.get_json(f"link:{short_code}")
    
    async def set_link(self, short_code: str, link_data: dict, expire: int = 3600) -> bool:
        """Кэширует данные ссылки."""
        return await self.set_json(f"link:{short_code}", link_data, expire)
    
    async def delete_link(self, short_code: str) -> int:
        """Удаляет ссылку из кэша."""
        return await self.delete(f"link:{short_code}")
    
    async def increment_click_count(self, short_code: str) -> int:
        """Инкрементирует количество кликов для ссылки."""
        return await self.increment(f"clicks:{short_code}")
    
    async def get_click_count(self, short_code: str) -> int:
        """Получает количество кликов из кэша."""
        count = await self.get(f"clicks:{short_code}")
        return int(count) if count else 0

# глобальный экземпляр CacheService 
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Получает глобальный экземпляр CacheService"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    return _cache_service
