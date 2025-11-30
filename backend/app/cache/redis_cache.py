"""Redis cache implementation for query caching and rate limiting."""
import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

from ..config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache with tenant isolation."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize Redis client."""
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.db = db if db is not None else settings.redis_db
        self.password = password or settings.redis_password
        self.ttl = settings.redis_ttl_seconds

        self.client: Redis = aioredis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )
        logger.info(f"Initialized Redis cache: {self.host}:{self.port}/{self.db}")

    def _get_cache_key(self, tenant_id: str, key: str) -> str:
        """Get tenant-prefixed cache key."""
        return f"tenant:{tenant_id}:cache:{key}"

    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query caching."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    async def get(self, tenant_id: str, key: str) -> Any | None:
        """Get value from cache."""
        try:
            cache_key = self._get_cache_key(tenant_id, key)
            value = await self.client.get(cache_key)

            if value:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(value)

            logger.debug(f"Cache miss: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None

    async def set(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache."""
        try:
            cache_key = self._get_cache_key(tenant_id, key)
            serialized_value = json.dumps(value)
            ttl_seconds = ttl or self.ttl

            await self.client.setex(cache_key, ttl_seconds, serialized_value)
            logger.debug(f"Cache set: {cache_key} (TTL: {ttl_seconds}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    async def delete(self, tenant_id: str, key: str) -> bool:
        """Delete value from cache."""
        try:
            cache_key = self._get_cache_key(tenant_id, key)
            await self.client.delete(cache_key)
            logger.debug(f"Cache deleted: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False

    async def get_query_cache(self, tenant_id: str, query: str) -> Any | None:
        """Get cached query result."""
        query_hash = self._get_query_hash(query)
        return await self.get(tenant_id, f"query:{query_hash}")

    async def set_query_cache(
        self,
        tenant_id: str,
        query: str,
        result: Any,
        ttl: int | None = None,
    ) -> bool:
        """Cache query result."""
        query_hash = self._get_query_hash(query)
        return await self.set(tenant_id, f"query:{query_hash}", result, ttl)

    async def get_tenant_balance(self, tenant_id: str) -> float:
        """Get tenant balance for cost tracking."""
        try:
            balance_key = f"tenant:{tenant_id}:balance"
            balance = await self.client.get(balance_key)
            return float(balance) if balance else 10000.0  # Default balance

        except Exception as e:
            logger.error(f"Failed to get tenant balance: {e}")
            return 10000.0

    async def deduct_tenant_balance(self, tenant_id: str, amount: float) -> float:
        """Deduct from tenant balance."""
        try:
            balance_key = f"tenant:{tenant_id}:balance"
            new_balance = await self.client.incrbyfloat(balance_key, -amount)
            logger.debug(f"Deducted ${amount:.4f} from tenant {tenant_id}, new balance: ${new_balance:.2f}")
            return new_balance

        except Exception as e:
            logger.error(f"Failed to deduct tenant balance: {e}")
            return 0.0

    async def check_rate_limit(
        self,
        tenant_id: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if tenant is within rate limit."""
        try:
            rate_key = f"tenant:{tenant_id}:rate:{window_seconds}"
            current = await self.client.get(rate_key)

            if current is None:
                # First request in window
                await self.client.setex(rate_key, window_seconds, "1")
                return True, limit - 1

            current_count = int(current)
            if current_count >= limit:
                return False, 0

            # Increment counter
            await self.client.incr(rate_key)
            return True, limit - current_count - 1

        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True, limit  # Fail open

    async def get_stats(self) -> dict[str, Any]:
        """Get Redis stats."""
        try:
            info = await self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                )
                * 100,
            }

        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {}

    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()
        logger.info("Closed Redis cache")
