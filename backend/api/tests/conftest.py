import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

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
