"""Redis-backed distributed rate limiter with sliding window algorithm."""
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request
from redis.asyncio import Redis

from .config import settings

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis with sliding window algorithm.
    
    Features:
    - Per-tenant rate limiting
    - Configurable window size and request limits
    - Atomic operations using Redis ZSET
    - Automatic cleanup of expired entries
    """
    
    def __init__(
        self,
        redis_client: Redis,
        window_seconds: int = 60,
        max_requests: int = 300
    ):
        self.redis = redis_client
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.key_prefix = "ratelimit"
    
    async def check_rate_limit(
        self,
        identifier: str,
        tenant_id: str,
        cost: int = 1
    ) -> dict[str, any]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (user_id, api_key, or IP)
            tenant_id: Tenant ID for multi-tenant isolation
            cost: Request cost (default 1, can be higher for expensive operations)
        
        Returns:
            Dict with limit info: {
                "allowed": bool,
                "current": int,
                "limit": int,
                "remaining": int,
                "reset_at": int
            }
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Redis key with tenant isolation
        key = f"{self.key_prefix}:{tenant_id}:{identifier}"
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove entries outside the sliding window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request with timestamp as score
            # Use microseconds for uniqueness
            request_id = f"{now}:{time.time_ns()}"
            pipe.zadd(key, {request_id: now})
            
            # Set expiration to window + buffer
            pipe.expire(key, self.window_seconds + 10)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Extract count (before adding current request)
            current_count = results[1]
            
            # Calculate limits
            new_count = current_count + cost
            remaining = max(0, self.max_requests - new_count)
            reset_at = int(now + self.window_seconds)
            
            result = {
                "allowed": new_count <= self.max_requests,
                "current": new_count,
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_at": reset_at,
                "window_seconds": self.window_seconds
            }
            
            if not result["allowed"]:
                # Remove the request we just added since it's denied
                await self.redis.zrem(key, request_id)
                
                logger.warning(
                    f"Rate limit exceeded for {identifier} (tenant: {tenant_id}): "
                    f"{new_count}/{self.max_requests} requests"
                )
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {int(reset_at - now)} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                        "Retry-After": str(int(reset_at - now))
                    }
                )
            
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiter error: {e}", exc_info=True)
            # Fail open - allow request if Redis is down (logged for monitoring)
            logger.warning("Rate limiter failed open - allowing request")
            return {
                "allowed": True,
                "current": 0,
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset_at": int(now + self.window_seconds),
                "window_seconds": self.window_seconds,
                "error": str(e)
            }
    
    async def get_limit_info(self, identifier: str, tenant_id: str) -> dict[str, any]:
        """Get current rate limit status without incrementing."""
        now = time.time()
        window_start = now - self.window_seconds
        
        key = f"{self.key_prefix}:{tenant_id}:{identifier}"
        
        try:
            # Clean up old entries
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Get current count
            current_count = await self.redis.zcard(key)
            
            remaining = max(0, self.max_requests - current_count)
            reset_at = int(now + self.window_seconds)
            
            return {
                "current": current_count,
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_at": reset_at,
                "window_seconds": self.window_seconds
            }
        
        except Exception as e:
            logger.error(f"Failed to get limit info: {e}", exc_info=True)
            return {
                "current": 0,
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset_at": int(now + self.window_seconds),
                "window_seconds": self.window_seconds,
                "error": str(e)
            }
    
    async def reset_limit(self, identifier: str, tenant_id: str) -> bool:
        """Reset rate limit for identifier (admin use)."""
        key = f"{self.key_prefix}:{tenant_id}:{identifier}"
        
        try:
            await self.redis.delete(key)
            logger.info(f"Rate limit reset for {identifier} (tenant: {tenant_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to reset limit: {e}", exc_info=True)
            return False


async def get_rate_limiter_dependency(request: Request) -> Optional[RedisRateLimiter]:
    """FastAPI dependency to get rate limiter instance."""
    # Get Redis client from app state (configured in lifespan)
    redis_client = getattr(request.app.state, "redis_client", None)
    
    if not redis_client:
        logger.warning("Redis client not available for rate limiting")
        return None
    
    return RedisRateLimiter(
        redis_client=redis_client,
        window_seconds=settings.rate_limit_window,
        max_requests=settings.rate_limit_max_requests
    )


async def rate_limit_middleware(
    request: Request,
    tenant_id: str,
    user_id: str = "anonymous"
) -> dict[str, any]:
    """
    Rate limit middleware for FastAPI endpoints.
    
    Usage in endpoint:
        @app.get("/api/v1/resource")
        async def resource(
            request: Request,
            tenant_id: str = Depends(get_tenant_id),
            current_user: dict = Depends(get_current_user)
        ):
            await rate_limit_middleware(request, tenant_id, current_user["user_id"])
            # ... endpoint logic
    """
    rate_limiter = await get_rate_limiter_dependency(request)
    
    if not rate_limiter:
        # Redis not available, skip rate limiting (fail open with warning)
        logger.warning("Rate limiting disabled - Redis unavailable")
        return {"allowed": True, "skip_reason": "redis_unavailable"}
    
    # Use user_id as primary identifier, fallback to IP
    identifier = user_id if user_id != "anonymous" else request.client.host
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit(identifier, tenant_id)
    
    # Add rate limit headers to response (done in middleware)
    request.state.rate_limit_info = result
    
    return result
