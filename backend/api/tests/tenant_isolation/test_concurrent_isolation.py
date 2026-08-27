import asyncio

from sqlalchemy import select

from app.documents.models import Document
from tests.tenant_isolation.conftest import tenant_session


async def _read_visible_docs(sessionmaker, tenant_id):
    async with tenant_session(sessionmaker, tenant_id) as session:
        result = await session.execute(select(Document))
        docs = result.scalars().all()
    return tenant_id, {doc.id for doc in docs}


async def test_concurrent_tenant_contexts_do_not_leak(app_sessionmaker_pooled, seeded_tenants):
    tenant_a = seeded_tenants["tenant_a"]
    tenant_b = seeded_tenants["tenant_b"]
    doc_a = seeded_tenants["doc_a"]
    doc_b = seeded_tenants["doc_b"]

    tasks = [
        _read_visible_docs(
            app_sessionmaker_pooled,
            tenant_a if i % 2 == 0 else tenant_b,
        )
        for i in range(30)
    ]

    results = await asyncio.gather(*tasks)

    for scoped_tenant, seen in results:
        if scoped_tenant == tenant_a:
            assert doc_a in seen
            assert doc_b not in seen
        else:
            assert doc_b in seen
            assert doc_a not in seen
