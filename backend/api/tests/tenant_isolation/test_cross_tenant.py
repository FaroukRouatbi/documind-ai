from sqlalchemy import select

from app.documents.models import Document
from tests.tenant_isolation.conftest import tenant_session


async def test_scoped_session_sees_only_own_tenant_documents(
        app_sessionmaker, seeded_tenants
):
    async with tenant_session(app_sessionmaker, seeded_tenants["tenant_a"]) as session:
        result = await session.execute(select(Document))
        docs = result.scalars().all()

    doc_ids = {doc.id for doc in docs}

    assert seeded_tenants["doc_a"] in doc_ids
    assert seeded_tenants["doc_b"] not in doc_ids