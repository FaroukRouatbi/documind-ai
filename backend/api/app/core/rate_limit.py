import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


async def check_rate_limit(
    client: redis.Redis | None,
    tenant_id: str,
    limit: int,
    window_seconds: int = 60,
) -> bool:
    if client is None:
        return True

    key = f"ratelimit:query:{tenant_id}"

    try:
        await client.set(key, 0, ex=window_seconds, nx=True)
        count = await client.incr(key)
    except Exception:
        logger.error("rate_limit_check_failed", tenant_id=tenant_id)
        return True

    return count <= limit
