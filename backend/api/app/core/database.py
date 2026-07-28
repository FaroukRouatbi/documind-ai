from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from app.core.config import settings
from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase

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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
) -> AsyncGenerator[AsyncSession, None]:
    tenant_id = current_user["tenant_id"]
    await session.execute(
    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
    {"tenant_id": tenant_id},
)
    yield session

from app.documents.models import Document  
from app.tenants.models import Tenant  
