from app.documents.repository import DocumentRepository
from tests.conftest import tenant_session


async def test_get_by_ids_does_not_return_other_tenants_documents(app_sessionmaker, seeded_tenants):
    tenant_b = seeded_tenants["tenant_b"]
    doc_a = seeded_tenants["doc_a"]
    doc_b = seeded_tenants["doc_b"]

    async with tenant_session(app_sessionmaker, tenant_b) as session:
        docs = await DocumentRepository(session).get_by_ids([doc_a, doc_b])

    returned_ids = {d.id for d in docs}
    assert doc_b in returned_ids  # B sees its own
    assert doc_a not in returned_ids  # RLS filters out A's, despite being asked for explicitly
