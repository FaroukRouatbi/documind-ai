from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from app.core.config import settings
from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase



DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db.username}:{settings.db.password}"
    f"@{settings.db.host}:{settings.db.port}/{settings.db.dbname}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

class Base(DeclarativeBase):
    pass