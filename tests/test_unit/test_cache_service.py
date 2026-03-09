"""Unit tests for CacheService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.exceptions import RedisError
import json

from src.services.cache_service import CacheService


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=False)
    redis.incr = AsyncMock(return_value=1)
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def cache_service(mock_redis):
    """Create CacheService with mocked Redis."""
    service = CacheService()
    service._redis = mock_redis
    return service


class TestCacheServiceBasicOperations:
    """Tests for basic cache operations."""
    
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, cache_service, mock_redis):
        """Test get returns None for missing key."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get("missing_key")
        
        assert result is None
        mock_redis.get.assert_called_with("missing_key")
    
    @pytest.mark.asyncio
    async def test_get_returns_value(self, cache_service, mock_redis):
        """Test get returns stored value."""
        mock_redis.get.return_value = "stored_value"
        
        result = await cache_service.get("existing_key")
        
        assert result == "stored_value"
    
    @pytest.mark.asyncio
    async def test_set_stores_value(self, cache_service, mock_redis):
        """Test set stores value."""
        result = await cache_service.set("new_key", "new_value", expire=3600)
        
        assert result is True
        mock_redis.set.assert_called_with("new_key", "new_value", ex=3600)
    
    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Test delete removes key."""
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete("key_to_delete")
        
        assert result == 1
        mock_redis.delete.assert_called_with("key_to_delete")
    
    @pytest.mark.asyncio
    async def test_exists_checks_key(self, cache_service, mock_redis):
        """Test exists checks for key presence."""
        mock_redis.exists.return_value = True
        
        result = await cache_service.exists("some_key")
        
        assert result is True
        mock_redis.exists.assert_called_with("some_key")


class TestCacheServiceJsonOperations:
    """Tests for JSON cache operations."""
    
    @pytest.mark.asyncio
    async def test_get_json_returns_parsed_data(self, cache_service, mock_redis):
        """Test get_json returns parsed JSON."""
        json_data = {"key": "value", "number": 42}
        mock_redis.get.return_value = json.dumps(json_data)
        
        result = await cache_service.get_json("json_key")
        
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_get_json_returns_none_for_missing(self, cache_service, mock_redis):
        """Test get_json returns None for missing key."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_json("missing_json_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_json_stores_serialized_data(self, cache_service, mock_redis):
        """Test set_json stores serialized JSON."""
        data = {"name": "test", "active": True}
        
        result = await cache_service.set_json("json_key", data, expire=3600)
        
        assert result is True
        expected_json = json.dumps(data)
        mock_redis.set.assert_called_with("json_key", expected_json, ex=3600)


class TestCacheServiceLinkOperations:
    """Tests for link-specific cache operations."""
    
    @pytest.mark.asyncio
    async def test_get_link_returns_cached_link(self, cache_service, mock_redis):
        """Test get_link returns cached link data."""
        link_data = {
            "original_url": "https://example.com",
            "short_code": "abc123",
            "click_count": 10
        }
        mock_redis.get.return_value = json.dumps(link_data)
        
        result = await cache_service.get_link("abc123")
        
        assert result == link_data
        mock_redis.get.assert_called_with("link:abc123")
    
    @pytest.mark.asyncio
    async def test_get_link_returns_none_when_not_cached(self, cache_service, mock_redis):
        """Test get_link returns None when not in cache."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_link("notcached")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_link_caches_link_data(self, cache_service, mock_redis):
        """Test set_link caches link data."""
        link_data = {
            "original_url": "https://example.com/new",
            "short_code": "new123"
        }
        
        result = await cache_service.set_link("new123", link_data)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_link_with_custom_expiry(self, cache_service, mock_redis):
        """Test set_link with custom expiry time."""
        link_data = {"original_url": "https://example.com"}
        
        result = await cache_service.set_link("exp123", link_data, expire=7200)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_link_removes_cached_link(self, cache_service, mock_redis):
        """Test delete_link removes cached link."""
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete_link("delete123")
        
        assert result == 1
        mock_redis.delete.assert_called_with("link:delete123")
    
    @pytest.mark.asyncio
    async def test_increment_click_count(self, cache_service, mock_redis):
        """Test incrementing click count."""
        mock_redis.incr.return_value = 42
        
        result = await cache_service.increment_click_count("click123")
        
        assert result == 42
        mock_redis.incr.assert_called_with("clicks:click123")
    
    @pytest.mark.asyncio
    async def test_get_click_count(self, cache_service, mock_redis):
        """Test getting click count."""
        mock_redis.get.return_value = "25"
        
        result = await cache_service.get_click_count("count123")
        
        assert result == 25


class TestCacheServiceErrorHandling:
    """Tests for cache error handling."""
    
    @pytest.mark.asyncio
    async def test_get_handles_redis_error(self, cache_service, mock_redis):
        """Test get handles Redis errors gracefully."""
        mock_redis.get.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.get("error_key")
        
        # Should return None instead of raising exception
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_handles_redis_error(self, cache_service, mock_redis):
        """Test set handles Redis errors gracefully."""
        mock_redis.set.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.set("error_key", "value")
        
        # Should return False instead of raising exception
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_handles_redis_error(self, cache_service, mock_redis):
        """Test delete handles Redis errors gracefully."""
        mock_redis.delete.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.delete("error_key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_exists_handles_redis_error(self, cache_service, mock_redis):
        """Test exists handles Redis errors gracefully."""
        mock_redis.exists.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.exists("error_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_increment_handles_redis_error(self, cache_service, mock_redis):
        """Test increment handles Redis errors gracefully."""
        mock_redis.incr.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.increment("error_key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_get_json_handles_invalid_json(self, cache_service, mock_redis):
        """Test get_json handles invalid JSON gracefully."""
        mock_redis.get.return_value = "not-valid-json{"
        
        result = await cache_service.get_json("bad_json_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_click_count_returns_zero_on_none(self, cache_service, mock_redis):
        """Test get_click_count returns 0 when not in cache."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_click_count("missing_key")
        
        assert result == 0


class TestCacheServiceConnectionManagement:
    """Tests for connection management."""
    
    @pytest.mark.asyncio
    async def test_disconnect_closes_redis(self, cache_service, mock_redis):
        """Test disconnect closes Redis connection."""
        await cache_service.disconnect()
        
        mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_handles_error(self, cache_service, mock_redis):
        """Test disconnect handles Redis error gracefully."""
        mock_redis.close.side_effect = RedisError("Close error")
        
        # Should not raise exception
        await cache_service.disconnect()
        
        # _redis should be cleared even on error
        assert cache_service._redis is None
    
    @pytest.mark.asyncio
    async def test_get_with_no_connection_tries_connect(self):
        """Test get tries to connect when _redis is None."""
        service = CacheService()
        service._redis = None
        
        # Patch connect so it sets a mock redis
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="value")
        
        async def mock_connect():
            service._redis = mock_redis
            
        with patch.object(service, 'connect', side_effect=mock_connect):
            result = await service.get("key")
        
        assert result == "value"
    
    @pytest.mark.asyncio  
    async def test_set_with_no_connection_returns_false(self):
        """Test set returns False when connection fails."""
        service = CacheService()
        service._redis = None
        
        # connect fails to establish connection
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.set("key", "value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_with_no_connection_returns_zero(self):
        """Test delete returns 0 when connection fails."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.delete("key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_exists_with_no_connection_returns_false(self):
        """Test exists returns False when connection fails."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.exists("key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_increment_with_no_connection_returns_zero(self):
        """Test increment returns 0 when connection fails."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.increment("key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_connect_handles_redis_error(self):
        """Test connect handles RedisError gracefully."""
        service = CacheService()
        
        with patch('src.services.cache_service.redis.from_url', 
                   side_effect=RedisError("Connection failed")):
            await service.connect()
        
        assert service._redis is None
    
    @pytest.mark.asyncio
    async def test_disconnect_when_no_connection(self):
        """Test disconnect does nothing when _redis is None."""
        service = CacheService()
        service._redis = None
        
        # Should not raise exception
        await service.disconnect()
        
        assert service._redis is None
