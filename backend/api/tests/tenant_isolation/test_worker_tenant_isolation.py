from app.documents.repository import DocumentRepository
from tests.conftest import tenant_session


async def test_worker_scoped_to_b_cannot_fetch_a_document_by_s3_key(
    app_sessionmaker, seeded_tenants
):
    async with tenant_session(app_sessionmaker, seeded_tenants["tenant_b"]) as session:
        repo = DocumentRepository(session)

        # B fetching A's document by its key → RLS refuses → None
        stolen = await repo.get_by_s3_key(seeded_tenants["doc_a_s3_key"])

        # B fetching its own document by key → returns the row
        own = await repo.get_by_s3_key(seeded_tenants["doc_b_s3_key"])

    assert stolen is None
    assert own is not None
    assert own.id == seeded_tenants["doc_b"]
