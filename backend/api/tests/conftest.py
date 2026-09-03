from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import DBCredentials, settings
from app.core.database import get_tenant_db
from app.core.security import get_current_user
from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def override_current_user():
    """Override auth to return a fixed fake tenant, no JWT needed."""

    async def _fake_current_user():
        return {"sub": "test-user", "tenant_id": TEST_TENANT_ID}

    app.dependency_overrides[get_current_user] = _fake_current_user
    yield TEST_TENANT_ID
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def override_tenant_db(app_sessionmaker):
    async def _get_test_tenant_db():
        async with tenant_session(app_sessionmaker, TEST_TENANT_ID) as session:
            yield session

    app.dependency_overrides[get_tenant_db] = _get_test_tenant_db
    yield
    app.dependency_overrides.pop(get_tenant_db, None)


def _url(creds: DBCredentials) -> str:
    return (
        f"postgresql+asyncpg://{creds.username}:{creds.password}"
        f"@{creds.host}:{creds.port}/{creds.dbname}"
    )


APP_URL = _url(settings.db)
OWNER_URL = _url(settings.migration_db)


@pytest_asyncio.fixture(scope="function")
async def owner_engine():
    engine = create_async_engine(OWNER_URL, poolclass=NullPool)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def app_engine():
    engine = create_async_engine(APP_URL, poolclass=NullPool)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def app_engine_pooled():
    engine = create_async_engine(
        APP_URL,
        pool_size=2,
        max_overflow=0,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def owner_sessionmaker(owner_engine):
    return async_sessionmaker(bind=owner_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def app_sessionmaker(app_engine):
    return async_sessionmaker(bind=app_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def app_sessionmaker_pooled(app_engine_pooled):
    return async_sessionmaker(bind=app_engine_pooled, expire_on_commit=False)


@asynccontextmanager
async def tenant_session(sessionmaker, tenant_id):
    async with sessionmaker() as session:
        async with session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
            )
            yield session
