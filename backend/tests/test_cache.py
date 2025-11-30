"""
Tests for Redis cache module
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import hashlib
from datetime import datetime, timedelta
from app.cache.redis_cache import RedisCache


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.incr.return_value = 1
    redis_mock.expire.return_value = True
    redis_mock.ttl.return_value = 3600
    redis_mock.info.return_value = {
        "used_memory": 1024 * 1024,
        "keyspace_hits": 1000,
        "keyspace_misses": 200
    }
    return redis_mock


@pytest.fixture
async def cache(mock_redis):
    """Create cache with mocked Redis"""
    with patch('redis.asyncio.from_url', return_value=mock_redis):
        cache_instance = RedisCache(redis_url="redis://localhost:6379")
        await cache_instance.connect()
        return cache_instance


@pytest.mark.asyncio
async def test_cache_connect(cache, mock_redis):
    """Test Redis connection"""
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_cache_disconnect(cache, mock_redis):
    """Test Redis disconnection"""
    await cache.disconnect()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_cache_get_query_cache_hit(cache, mock_redis):
    """Test cache hit for query"""
    # Arrange
    tenant_id = "test-tenant"
    query = "What are security requirements?"
    cached_response = {
        "answer": "Security requirements include...",
        "citations": [],
        "cached": True
    }
    mock_redis.get.return_value = json.dumps(cached_response)
    
    # Act
    result = await cache.get_query_cache(tenant_id, query)
    
    # Assert
    assert result is not None
    assert result["answer"] == "Security requirements include..."
    assert result["cached"] is True
    
    # Verify cache key format
    expected_key = f"tenant:{tenant_id}:query:{hashlib.sha256(query.encode()).hexdigest()}"
    mock_redis.get.assert_called_once_with(expected_key)


@pytest.mark.asyncio
async def test_cache_get_query_cache_miss(cache, mock_redis):
    """Test cache miss for query"""
    # Arrange
    mock_redis.get.return_value = None
    
    # Act
    result = await cache.get_query_cache("test-tenant", "New query")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_query_cache(cache, mock_redis):
    """Test setting query cache"""
    # Arrange
    tenant_id = "test-tenant"
    query = "Test query"
    response = {"answer": "Test answer", "citations": []}
    ttl = 3600
    
    # Act
    await cache.set_query_cache(tenant_id, query, response, ttl)
    
    # Assert
    expected_key = f"tenant:{tenant_id}:query:{hashlib.sha256(query.encode()).hexdigest()}"
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == expected_key
    assert json.loads(call_args[0][1]) == response
    assert call_args[1]["ex"] == ttl


@pytest.mark.asyncio
async def test_cache_rate_limit_check_allowed(cache, mock_redis):
    """Test rate limit check - request allowed"""
    # Arrange
    tenant_id = "test-tenant"
    mock_redis.incr.return_value = 50  # Under limit
    
    # Act
    is_allowed = await cache.check_rate_limit(tenant_id, limit=100, window=60)
    
    # Assert
    assert is_allowed is True
    expected_key = f"tenant:{tenant_id}:rate_limit"
    mock_redis.incr.assert_called_once_with(expected_key)


@pytest.mark.asyncio
async def test_cache_rate_limit_check_exceeded(cache, mock_redis):
    """Test rate limit check - limit exceeded"""
    # Arrange
    tenant_id = "test-tenant"
    mock_redis.incr.return_value = 101  # Over limit
    
    # Act
    is_allowed = await cache.check_rate_limit(tenant_id, limit=100, window=60)
    
    # Assert
    assert is_allowed is False


@pytest.mark.asyncio
async def test_cache_rate_limit_sets_expiry(cache, mock_redis):
    """Test that rate limit key gets expiry set"""
    # Arrange
    mock_redis.incr.return_value = 1  # First request
    mock_redis.ttl.return_value = -1  # No expiry set
    
    # Act
    await cache.check_rate_limit("test-tenant", limit=100, window=60)
    
    # Assert
    mock_redis.expire.assert_called_once()


@pytest.mark.asyncio
async def test_cache_get_tenant_balance(cache, mock_redis):
    """Test getting tenant balance"""
    # Arrange
    tenant_id = "test-tenant"
    mock_redis.get.return_value = "100.50"
    
    # Act
    balance = await cache.get_tenant_balance(tenant_id)
    
    # Assert
    assert balance == 100.50
    expected_key = f"tenant:{tenant_id}:balance"
    mock_redis.get.assert_called_once_with(expected_key)


@pytest.mark.asyncio
async def test_cache_get_tenant_balance_default(cache, mock_redis):
    """Test getting tenant balance with default value"""
    # Arrange
    mock_redis.get.return_value = None
    
    # Act
    balance = await cache.get_tenant_balance("test-tenant", default_balance=1000.0)
    
    # Assert
    assert balance == 1000.0


@pytest.mark.asyncio
async def test_cache_deduct_tenant_balance(cache, mock_redis):
    """Test deducting from tenant balance"""
    # Arrange
    tenant_id = "test-tenant"
    mock_redis.get.return_value = "100.00"
    amount = 0.05
    
    # Act
    new_balance = await cache.deduct_tenant_balance(tenant_id, amount)
    
    # Assert
    assert new_balance == 99.95
    expected_key = f"tenant:{tenant_id}:balance"
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == expected_key
    assert float(call_args[0][1]) == 99.95


@pytest.mark.asyncio
async def test_cache_deduct_balance_insufficient_funds(cache, mock_redis):
    """Test deducting more than available balance"""
    # Arrange
    mock_redis.get.return_value = "0.01"
    
    # Act
    new_balance = await cache.deduct_tenant_balance("test-tenant", 10.0)
    
    # Assert - Should allow negative balance but track it
    assert new_balance < 0


@pytest.mark.asyncio
async def test_cache_get_stats(cache, mock_redis):
    """Test getting cache statistics"""
    # Arrange
    mock_redis.info.return_value = {
        "used_memory": 10485760,  # 10 MB
        "keyspace_hits": 8000,
        "keyspace_misses": 2000
    }
    
    # Act
    stats = await cache.get_stats()
    
    # Assert
    assert stats["memory_usage_mb"] == 10.0
    assert stats["total_commands"] == 10000
    assert stats["hit_rate"] == 0.8  # 8000 / 10000


@pytest.mark.asyncio
async def test_cache_get_stats_no_misses(cache, mock_redis):
    """Test stats calculation with no cache misses"""
    # Arrange
    mock_redis.info.return_value = {
        "used_memory": 1024,
        "keyspace_hits": 100,
        "keyspace_misses": 0
    }
    
    # Act
    stats = await cache.get_stats()
    
    # Assert
    assert stats["hit_rate"] == 1.0


@pytest.mark.asyncio
async def test_cache_tenant_isolation(cache, mock_redis):
    """Test that cache keys are tenant-isolated"""
    # Arrange
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"
    query = "Same query"
    
    # Act
    await cache.get_query_cache(tenant_a, query)
    await cache.get_query_cache(tenant_b, query)
    
    # Assert - Different cache keys for different tenants
    calls = mock_redis.get.call_args_list
    key_a = calls[0][0][0]
    key_b = calls[1][0][0]
    assert key_a != key_b
    assert "tenant-a" in key_a
    assert "tenant-b" in key_b


@pytest.mark.asyncio
async def test_cache_handles_redis_error(cache, mock_redis):
    """Test error handling when Redis fails"""
    # Arrange
    mock_redis.get.side_effect = Exception("Redis connection failed")
    
    # Act & Assert
    with pytest.raises(Exception, match="Redis connection failed"):
        await cache.get_query_cache("test-tenant", "query")


@pytest.mark.asyncio
async def test_cache_get_tenant_stats(cache, mock_redis):
    """Test getting per-tenant statistics"""
    # Arrange
    tenant_id = "test-tenant"
    mock_redis.get.return_value = "95.50"  # Balance
    
    # Act
    stats = await cache.get_tenant_stats(tenant_id)
    
    # Assert
    assert "balance" in stats
    assert stats["balance"] == 95.50


@pytest.mark.asyncio
async def test_cache_query_hash_consistency(cache):
    """Test that same query produces same hash"""
    # Arrange
    query = "Test query"
    
    # Act - Hash the query twice
    hash1 = hashlib.sha256(query.encode()).hexdigest()
    hash2 = hashlib.sha256(query.encode()).hexdigest()
    
    # Assert
    assert hash1 == hash2
