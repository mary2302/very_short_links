"""Redis cache service for caching popular links."""

import json
import logging
from typing import Optional
import redis.asyncio as redis
from redis.exceptions import RedisError
from src.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis cache operations."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
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
        """Close Redis connection."""
        if self._redis:
            try:
                await self._redis.close()
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache. Returns None on Redis errors (graceful degradation)."""
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
        """Set value in cache with expiration. Returns False on Redis errors."""
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
        """Delete key from cache. Returns 0 on Redis errors."""
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
        """Check if key exists in cache. Returns False on Redis errors."""
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
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for key '{key}': {e}")
                return None
        return None
    
    async def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """Set JSON value in cache."""
        return await self.set(key, json.dumps(value), expire)
    
    async def increment(self, key: str) -> int:
        """Increment a counter in cache. Returns 0 on Redis errors."""
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
        """Get cached link data."""
        return await self.get_json(f"link:{short_code}")
    
    async def set_link(self, short_code: str, link_data: dict, expire: int = 3600) -> bool:
        """Cache link data."""
        return await self.set_json(f"link:{short_code}", link_data, expire)
    
    async def delete_link(self, short_code: str) -> int:
        """Remove link from cache."""
        return await self.delete(f"link:{short_code}")
    
    async def increment_click_count(self, short_code: str) -> int:
        """Increment click count for a link."""
        return await self.increment(f"clicks:{short_code}")
    
    async def get_click_count(self, short_code: str) -> int:
        """Get cached click count."""
        count = await self.get(f"clicks:{short_code}")
        return int(count) if count else 0


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    return _cache_service
