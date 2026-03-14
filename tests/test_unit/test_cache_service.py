import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.exceptions import RedisError
import json

from src.services.cache_service import CacheService


@pytest.fixture
def mock_redis():
    """Создает мок Redis клиента для тестирования CacheService."""
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
    """Создает CacheService с мокированным Redis."""
    service = CacheService()
    service._redis = mock_redis
    return service


class TestCacheServiceBasicOperations:
    """Тесты для базовых операций CacheService: get, set, delete, exists."""
    
    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_found(self, cache_service, mock_redis):
        """Тест get возвращает None, если ключ не найден."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get("missing_key")
        
        assert result is None
        mock_redis.get.assert_called_with("missing_key")
    
    @pytest.mark.asyncio
    async def test_get_returns_value(self, cache_service, mock_redis):
        """Тест get возвращает сохраненное значение."""
        mock_redis.get.return_value = "stored_value"
        
        result = await cache_service.get("existing_key")
        
        assert result == "stored_value"
    
    @pytest.mark.asyncio
    async def test_set_stores_value(self, cache_service, mock_redis):
        """Тест set сохраняет значение."""
        result = await cache_service.set("new_key", "new_value", expire=3600)
        
        assert result is True
        mock_redis.set.assert_called_with("new_key", "new_value", ex=3600)
    
    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_service, mock_redis):
        """Тест delete удаляет ключ."""
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete("key_to_delete")
        
        assert result == 1
        mock_redis.delete.assert_called_with("key_to_delete")
    
    @pytest.mark.asyncio
    async def test_exists_checks_key(self, cache_service, mock_redis):
        """Тест exists проверяет наличие ключа."""
        mock_redis.exists.return_value = True
        
        result = await cache_service.exists("some_key")
        
        assert result is True
        mock_redis.exists.assert_called_with("some_key")


class TestCacheServiceJsonOperations:
    """Тесты для операций кэширования JSON."""
    
    @pytest.mark.asyncio
    async def test_get_json_returns_parsed_data(self, cache_service, mock_redis):
        """Тест get_json возвращает разобранный JSON."""
        json_data = {"key": "value", "number": 42}
        mock_redis.get.return_value = json.dumps(json_data)
        
        result = await cache_service.get_json("json_key")
        
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_get_json_returns_none_for_missing(self, cache_service, mock_redis):
        """Тест get_json возвращает None для отсутствующего ключа."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_json("missing_json_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_json_stores_serialized_data(self, cache_service, mock_redis):
        """Тест set_json сохраняет сериализованный JSON."""
        data = {"name": "test", "active": True}
        
        result = await cache_service.set_json("json_key", data, expire=3600)
        
        assert result is True
        expected_json = json.dumps(data)
        mock_redis.set.assert_called_with("json_key", expected_json, ex=3600)


class TestCacheServiceLinkOperations:
    """Тесты для операций кэширования ссылок."""
    
    @pytest.mark.asyncio
    async def test_get_link_returns_cached_link(self, cache_service, mock_redis):
        """Тест get_link возвращает кэшированные данные ссылки."""
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
        """Тест get_link возвращает None, если ссылка не закэширована."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_link("notcached")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_link_caches_link_data(self, cache_service, mock_redis):
        """Тест set_link кэширует данные ссылки."""
        link_data = {
            "original_url": "https://example.com/new",
            "short_code": "new123"
        }
        
        result = await cache_service.set_link("new123", link_data)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_link_with_custom_expiry(self, cache_service, mock_redis):
        """Тест set_link с пользовательским временем истечения."""
        link_data = {"original_url": "https://example.com"}
        
        result = await cache_service.set_link("exp123", link_data, expire=7200)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_link_removes_cached_link(self, cache_service, mock_redis):
        """Тест delete_link удаляет кэшированную ссылку."""
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete_link("delete123")
        
        assert result == 1
        mock_redis.delete.assert_called_with("link:delete123")
    
    @pytest.mark.asyncio
    async def test_increment_click_count(self, cache_service, mock_redis):
        """Тест увеличения счетчика кликов."""
        mock_redis.incr.return_value = 42
        
        result = await cache_service.increment_click_count("click123")
        
        assert result == 42
        mock_redis.incr.assert_called_with("clicks:click123")
    
    @pytest.mark.asyncio
    async def test_get_click_count(self, cache_service, mock_redis):
        """Тест получения счетчика кликов."""
        mock_redis.get.return_value = "25"
        
        result = await cache_service.get_click_count("count123")
        
        assert result == 25


class TestCacheServiceErrorHandling:
    """Тесты для проверки обработки ошибок Redis в CacheService."""
    
    @pytest.mark.asyncio
    async def test_get_handles_redis_error(self, cache_service, mock_redis):
        """Тест get обрабатывает ошибки Redis верно"""
        mock_redis.get.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.get("error_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_handles_redis_error(self, cache_service, mock_redis):
        """Тест set обрабатывает ошибки Redis верно."""
        mock_redis.set.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.set("error_key", "value")

        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_handles_redis_error(self, cache_service, mock_redis):
        """Тест delete обрабатывает ошибки Redis верно."""
        mock_redis.delete.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.delete("error_key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_exists_handles_redis_error(self, cache_service, mock_redis):
        """Тест exists обрабатывает ошибки Redis верно."""
        mock_redis.exists.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.exists("error_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_increment_handles_redis_error(self, cache_service, mock_redis):
        """Тест increment обрабатывает ошибки Redis верно."""
        mock_redis.incr.side_effect = RedisError("Redis connection error")
        
        result = await cache_service.increment("error_key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_get_json_handles_invalid_json(self, cache_service, mock_redis):
        """Тест get_json обрабатывает некорректный JSON."""
        mock_redis.get.return_value = "not-valid-json{"
        
        result = await cache_service.get_json("bad_json_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_click_count_returns_zero_on_none(self, cache_service, mock_redis):
        """Тест get_click_count возвращает 0, если ключ не найден."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get_click_count("missing_key")
        
        assert result == 0


class TestCacheServiceConnectionManagement:
    """Тесты для управления подключениями."""
    
    @pytest.mark.asyncio
    async def test_disconnect_closes_redis(self, cache_service, mock_redis):
        """Тест отключения закрывает соединение Redis."""
        await cache_service.disconnect()
        
        mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_handles_error(self, cache_service, mock_redis):
        """Тест отключения обрабатывает ошибку Redis."""
        mock_redis.close.side_effect = RedisError("Close error")
        
        # Не должно выбрасывать исключение
        await cache_service.disconnect()
        
        # _redis должен быть None даже при ошибке
        assert cache_service._redis is None
    
    @pytest.mark.asyncio
    async def test_get_with_no_connection_tries_connect(self):
        """Тест get пытается подключиться, когда _redis равен None."""
        service = CacheService()
        service._redis = None
        
        # Мокаем connect, чтобы установить mock_redis при попытке подключения
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="value")
        
        async def mock_connect():
            service._redis = mock_redis
            
        with patch.object(service, 'connect', side_effect=mock_connect):
            result = await service.get("key")
        
        assert result == "value"
    
    @pytest.mark.asyncio  
    async def test_set_with_no_connection_returns_false(self):
        """Тест set возвращает False, когда подключение не установлено."""
        service = CacheService()
        service._redis = None
        
        # Мокаем connect, чтобы не устанавливать соединение
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.set("key", "value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_with_no_connection_returns_zero(self):
        """Тест delete возвращает 0, когда подключение не установлено."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.delete("key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_exists_with_no_connection_returns_false(self):
        """Тест exists возвращает False, когда подключение не установлено."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.exists("key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_increment_with_no_connection_returns_zero(self):
        """Тест increment возвращает 0, когда подключение не установлено."""
        service = CacheService()
        service._redis = None
        
        with patch.object(service, 'connect', new=AsyncMock()):
            result = await service.increment("key")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_connect_handles_redis_error(self):
        """Тест connect обрабатывает RedisError gracefully."""
        service = CacheService()
        
        with patch('src.services.cache_service.redis.from_url', 
                   side_effect=RedisError("Connection failed")):
            await service.connect()
        
        assert service._redis is None
    
    @pytest.mark.asyncio
    async def test_disconnect_when_no_connection(self):
        """Тест отключения не делает ничего, когда _redis равен None."""
        service = CacheService()
        service._redis = None
        
        await service.disconnect()
        assert service._redis is None
