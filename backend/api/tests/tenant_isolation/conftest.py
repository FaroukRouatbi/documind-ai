from contextlib import asynccontextmanager

import pytest_asyncio
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import DBCredentials, settings
from app.documents.models import Document
from app.tenants.models import Tenant


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


@pytest_asyncio.fixture
async def seeded_tenants(owner_sessionmaker):
    async with owner_sessionmaker() as session:
        async with session.begin():
            tenant_a = Tenant(name="Tenant A")
            tenant_b = Tenant(name="Tenant B")
            session.add_all([tenant_a, tenant_b])
            await session.flush()

            doc_a = Document(
                tenant_id=tenant_a.id,
                filename="a.md",
                s3_key=f"{tenant_a.id}/a.md",
                modality="text",
            )
            doc_b = Document(
                tenant_id=tenant_b.id,
                filename="b.md",
                s3_key=f"{tenant_b.id}/b.md",
                modality="text",
            )
            session.add_all([doc_a, doc_b])
            await session.flush()

            data = {
                "tenant_a": tenant_a.id,
                "tenant_b": tenant_b.id,
                "doc_a": doc_a.id,
                "doc_b": doc_b.id,
                "doc_a_s3_key": doc_a.s3_key,
                "doc_b_s3_key": doc_b.s3_key,
            }

    yield data

    async with owner_sessionmaker() as session:
        async with session.begin():
            await session.execute(
                text("DELETE FROM documents WHERE tenant_id = ANY(:ids)"),
                {"ids": [data["tenant_a"], data["tenant_b"]]},
            )
            await session.execute(
                text("DELETE FROM tenants WHERE id = ANY(:ids)"),
                {"ids": [data["tenant_a"], data["tenant_b"]]},
            )
