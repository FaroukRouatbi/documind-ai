import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.security import get_current_user


class Base(DeclarativeBase):
    pass

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db.username}:{settings.db.password}"
    f"@{settings.db.host}:{settings.db.port}/{settings.db.dbname}"
)

engine = create_async_engine(DATABASE_URL,
                             echo= settings.environment != "prod",
                             pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_tenant_db(
        session: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession]:
    tenant_id = current_user["tenant_id"]
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": tenant_id},
)
    yield session

@asynccontextmanager
async def get_worker_session(tenant_id: uuid.UUID) -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)}
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
