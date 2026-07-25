from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from app.core.config import settings
from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase



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
        except Exception:
            await session.rollback()
            raise

class Base(DeclarativeBase):
    pass