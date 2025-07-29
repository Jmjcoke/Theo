"""
Redis client connection and utilities
Manages Redis connection pool and basic operations
"""

import redis
import logging
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager
from redis.asyncio import Redis as AsyncRedis, ConnectionPool
from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with connection management"""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[AsyncRedis] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection pool"""
        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                password=settings.redis_password,
                max_connections=settings.redis_max_connections,
                retry_on_timeout=True,
                retry_on_error=[redis.exceptions.BusyLoadingError],
                encoding="utf-8",
                decode_responses=True
            )
            
            self._client = AsyncRedis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection pool"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        logger.info("Redis connection closed")
    
    @property
    def client(self) -> AsyncRedis:
        """Get Redis client instance"""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            await self.client.ping()
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global Redis client instance
redis_client = RedisClient()


@asynccontextmanager
async def get_redis():
    """Context manager for Redis operations"""
    try:
        yield redis_client.client
    except Exception as e:
        logger.error(f"Redis operation failed: {e}")
        raise