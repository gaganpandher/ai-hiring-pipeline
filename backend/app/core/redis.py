import redis.asyncio as aioredis
from app.core.config import settings
from loguru import logger

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency – returns a shared Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def init_redis():
    """Called on app startup to verify connection."""
    client = await get_redis()
    try:
        await client.ping()
        logger.info("✅ Redis connection OK")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise


async def close_redis():
    """Called on app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


# ─── Cache helpers ────────────────────────────────────────

async def cache_set(key: str, value: str, ttl: int = 300):
    client = await get_redis()
    await client.setex(key, ttl, value)


async def cache_get(key: str) -> str | None:
    client = await get_redis()
    return await client.get(key)


async def cache_delete(key: str):
    client = await get_redis()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    client = await get_redis()
    return bool(await client.exists(key))
