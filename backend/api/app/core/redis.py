import redis.asyncio as redis

from app.core.config import settings


def create_redis_client() -> redis.Redis | None:
    if not settings.redis_url:
        return None

    return redis.from_url(
        settings.redis_url,
        password=settings.redis_auth_token,
        decode_responses=True,
    )
