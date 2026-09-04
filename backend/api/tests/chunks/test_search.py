from sqlalchemy import text

from app.chunks.models import Chunk
from app.chunks.repository import ChunkRepository
from tests.conftest import tenant_session


def _unit_vector(dim, size=1024):
    vec = [0.0] * size
    vec[dim] = 1.0
    return vec


async def test_search_returns_nearest_chunk_first(
    owner_sessionmaker, app_sessionmaker, seeded_tenants
):
    tenant_a = seeded_tenants["tenant_a"]
    doc_a = seeded_tenants["doc_a"]

    # Seed 3 chunks as owner, each pointing along a different orthogonal axis
    async with owner_sessionmaker() as session:
        async with session.begin():
            for axis in (0, 1, 2):
                chunk = Chunk(
                    tenant_id=tenant_a,
                    document_id=doc_a,
                    chunk_index=axis,
                    content=f"chunk-axis-{axis}",
                    embedding=_unit_vector(axis),
                    embedding_model="test",
                    embedding_version="v1",
                    ingestion_strategy="text",
                )
                session.add(chunk)
            await session.flush()

    # Search as tenant A with a query pointing along axis 0
    async with tenant_session(app_sessionmaker, tenant_a) as session:
        repo = ChunkRepository(session)
        results = await repo.search(_unit_vector(0), k=3)

    # The axis-0 chunk is identical to the query → distance 0 → ranks first
    assert results[0].content == "chunk-axis-0"

    # cleanup: delete the seeded chunks as owner
    async with owner_sessionmaker() as session:
        async with session.begin():
            await session.execute(
                text("DELETE FROM chunks WHERE document_id = :doc"),
                {"doc": doc_a},
            )
