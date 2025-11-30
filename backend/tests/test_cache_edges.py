import json
import pytest
from unittest.mock import AsyncMock

from app.cache.redis_cache import RedisCache


@pytest.fixture()
def cache():
    c = RedisCache()
    # Replace underlying client with AsyncMock methods
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.setex = AsyncMock()
    mock.delete = AsyncMock()
    mock.incr = AsyncMock()
    mock.incrbyfloat = AsyncMock()
    mock.info = AsyncMock()
    c.client = mock
    return c

@pytest.mark.asyncio
async def test_rate_limit_first_request(cache):
    cache.client.get.return_value = None
    allowed, remaining = await cache.check_rate_limit("t1", limit=5, window_seconds=60)
    assert allowed is True and remaining == 4

@pytest.mark.asyncio
async def test_rate_limit_exhausted(cache):
    cache.client.get.return_value = "5"  # already at limit
    allowed, remaining = await cache.check_rate_limit("t1", limit=5, window_seconds=60)
    assert allowed is False and remaining == 0

@pytest.mark.asyncio
async def test_rate_limit_fail_open(cache):
    cache.client.get.side_effect = Exception("redis down")
    allowed, remaining = await cache.check_rate_limit("t1", limit=7, window_seconds=60)
    assert allowed is True and remaining == 7  # fail open path

@pytest.mark.asyncio
async def test_cache_get_hit_and_miss(cache):
    payload = {"answer": "hi"}
    cache.client.get.side_effect = [json.dumps(payload), None]
    v1 = await cache.get("tenantA", "key1")
    v2 = await cache.get("tenantA", "key1")
    assert v1 == payload and v2 is None

@pytest.mark.asyncio
async def test_cache_set_failure(cache):
    cache.client.setex.side_effect = Exception("write failed")
    ok = await cache.set("tenantA", "k", {"x": 1})
    assert ok is False

@pytest.mark.asyncio
async def test_balance_default_and_deduction(cache):
    # Default when missing
    cache.client.get.return_value = None
    bal = await cache.get_tenant_balance("tenantA")
    assert bal == 10000.0
    # Deduct path
    cache.client.incrbyfloat.return_value = -50.0
    new_bal = await cache.deduct_tenant_balance("tenantA", 50.0)
    assert new_bal == -50.0

@pytest.mark.asyncio
async def test_balance_existing(cache):
    cache.client.get.return_value = "123.45"
    bal = await cache.get_tenant_balance("tenantA")
    assert bal == 123.45

@pytest.mark.asyncio
async def test_stats_success_and_failure(cache):
    cache.client.info.side_effect = [
        {
            "connected_clients": 3,
            "used_memory_human": "1M",
            "total_commands_processed": 10,
            "keyspace_hits": 8,
            "keyspace_misses": 2,
        },
        Exception("stats error"),
    ]
    stats1 = await cache.get_stats()
    stats2 = await cache.get_stats()
    assert stats1["hit_rate"] == pytest.approx(80.0)
    assert stats2 == {}
