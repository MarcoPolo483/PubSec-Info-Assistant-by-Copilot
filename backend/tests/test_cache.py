"""Updated tests for RedisCache matching current implementation."""
import json
import hashlib
from unittest.mock import AsyncMock, patch

import pytest

from app.cache.redis_cache import RedisCache


@pytest.fixture
def mock_client():
    client = AsyncMock()
    # Default behaviors
    client.get.return_value = None
    client.setex.return_value = True
    client.delete.return_value = 1
    client.incr.return_value = 2
    client.incrbyfloat.return_value = 9999.5
    client.info.return_value = {
        "connected_clients": 5,
        "used_memory_human": "5M",
        "total_commands_processed": 1000,
        "keyspace_hits": 800,
        "keyspace_misses": 200,
    }
    return client


@pytest.fixture
def cache(mock_client):
    with patch("redis.asyncio.Redis", return_value=mock_client):
        return RedisCache(host="localhost", port=6379, db=0, password=None)


@pytest.mark.asyncio
async def test_set_and_get(cache, mock_client):
    tenant = "t1"
    key = "alpha"
    value = {"x": 1}
    await cache.set(tenant, key, value, ttl=42)
    mock_client.setex.assert_called_once()
    args = mock_client.setex.call_args[0]
    assert f"tenant:{tenant}:cache:{key}" == args[0]
    assert json.loads(args[2]) == value
    assert mock_client.setex.call_args[0][1] == 42
    # Simulate hit
    mock_client.get.return_value = json.dumps(value)
    result = await cache.get(tenant, key)
    assert result == value


@pytest.mark.asyncio
async def test_get_query_cache_hash(cache, mock_client):
    tenant = "tenant-x"
    query = "What is zero trust?"
    hashed = cache._get_query_hash(query)  # internal helper
    assert len(hashed) == 16
    mock_client.get.return_value = json.dumps({"answer": "Zero Trust"})
    result = await cache.get_query_cache(tenant, query)
    assert result["answer"] == "Zero Trust"
    mock_client.get.assert_called_once_with(f"tenant:{tenant}:cache:query:{hashed}")


@pytest.mark.asyncio
async def test_set_query_cache(cache, mock_client):
    tenant = "t2"
    query = "Explain FISMA"
    data = {"answer": "FISMA governs federal information security."}
    await cache.set_query_cache(tenant, query, data, ttl=10)
    hashed = cache._get_query_hash(query)
    mock_client.setex.assert_called_once()
    key_used = mock_client.setex.call_args[0][0]
    assert key_used.endswith(f"query:{hashed}")


@pytest.mark.asyncio
async def test_rate_limit_first_request(cache, mock_client):
    # First request: get returns None => setex used
    mock_client.get.return_value = None
    allowed, remaining = await cache.check_rate_limit("tenant-a", limit=5, window_seconds=60)
    assert allowed is True
    assert remaining == 4
    mock_client.setex.assert_called()  # new counter initialized


@pytest.mark.asyncio
async def test_rate_limit_increment(cache, mock_client):
    mock_client.get.return_value = "2"  # existing count
    allowed, remaining = await cache.check_rate_limit("tenant-a", limit=5, window_seconds=60)
    assert allowed is True
    assert remaining == 2  # 5 - 2 - 1 after increment
    mock_client.incr.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_exceeded(cache, mock_client):
    mock_client.get.return_value = "5"
    allowed, remaining = await cache.check_rate_limit("tenant-a", limit=5, window_seconds=60)
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_rate_limit_fail_open_on_exception(cache, mock_client):
    mock_client.get.side_effect = Exception("Redis down")
    allowed, remaining = await cache.check_rate_limit("tenant-a", limit=5, window_seconds=60)
    assert allowed is True  # fail open
    assert remaining == 5


@pytest.mark.asyncio
async def test_delete(cache, mock_client):
    ok = await cache.delete("tenant-a", "obsolete")
    assert ok is True
    mock_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats(cache, mock_client):
    stats = await cache.get_stats()
    assert stats["connected_clients"] == 5
    assert stats["hit_rate"] == pytest.approx(80.0)


@pytest.mark.asyncio
async def test_deduct_tenant_balance(cache, mock_client):
    new_balance = await cache.deduct_tenant_balance("tenant-a", 0.5)
    assert new_balance == 9999.5
    mock_client.incrbyfloat.assert_called_once()


@pytest.mark.asyncio
async def test_get_tenant_balance_default(cache, mock_client):
    mock_client.get.return_value = None
    balance = await cache.get_tenant_balance("tenant-a")
    assert balance == 10000.0


@pytest.mark.asyncio
async def test_get_tenant_balance_existing(cache, mock_client):
    mock_client.get.return_value = "123.45"
    balance = await cache.get_tenant_balance("tenant-a")
    assert balance == 123.45


@pytest.mark.asyncio
async def test_get_handles_exception(cache, mock_client):
    mock_client.get.side_effect = Exception("Failure")
    value = await cache.get("tenant-a", "any")
    assert value is None
