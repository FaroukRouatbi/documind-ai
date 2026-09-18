import pytest_asyncio

from app.core.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_app_engine():
    """process_upload uses the module-level production engine; dispose it
    between tests so pooled connections aren't reused across event loops."""
    yield
    await engine.dispose()
