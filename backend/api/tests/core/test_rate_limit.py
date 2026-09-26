import uuid

from app.core.rate_limit import check_rate_limit


async def test_requests_under_the_limit_are_allowed(redis_client):
    tenant = str(uuid.uuid4())

    for _ in range(3):
        assert await check_rate_limit(redis_client, tenant, limit=5) is True


async def test_requests_over_the_limit_are_rejected(redis_client):
    tenant = str(uuid.uuid4())

    for _ in range(5):
        assert await check_rate_limit(redis_client, tenant, limit=5) is True

    assert await check_rate_limit(redis_client, tenant, limit=5) is False


async def test_tenants_are_limited_independently(redis_client):
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    for _ in range(5):
        await check_rate_limit(redis_client, tenant_a, limit=5)
    assert await check_rate_limit(redis_client, tenant_a, limit=5) is False

    assert await check_rate_limit(redis_client, tenant_b, limit=5) is True


async def test_no_redis_client_allows_everything():
    assert await check_rate_limit(None, "any-tenant", limit=1) is True


async def test_counter_key_has_a_ttl(redis_client):
    tenant = str(uuid.uuid4())

    await check_rate_limit(redis_client, tenant, limit=5)

    ttl = await redis_client.ttl(f"ratelimit:query:{tenant}")
    assert 0 < ttl <= 60
