from app.chunks.models import Chunk
from app.chunks.repository import ChunkRepository
from tests.conftest import tenant_session


def _unit_vector(dim, size=1024):
    vec = [0.0] * size
    vec[dim] = 1.0
    return vec


async def test_search_returns_nearest_chunk_first(app_sessionmaker, seeded_tenants, seed_chunks):
    tenant_a = seeded_tenants["tenant_a"]
    doc_a = seeded_tenants["doc_a"]

    await seed_chunks(
        [
            Chunk(
                tenant_id=tenant_a,
                document_id=doc_a,
                chunk_index=axis,
                content=f"chunk-axis-{axis}",
                embedding=_unit_vector(axis),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            )
            for axis in (0, 1, 2)
        ]
    )

    async with tenant_session(app_sessionmaker, tenant_a) as session:
        results = await ChunkRepository(session).search(_unit_vector(0), k=3)

    assert results[0].content == "chunk-axis-0"


async def test_search_does_not_leak_other_tenant_chunks(
    app_sessionmaker, seeded_tenants, seed_chunks
):
    tenant_a, tenant_b = seeded_tenants["tenant_a"], seeded_tenants["tenant_b"]
    doc_a, doc_b = seeded_tenants["doc_a"], seeded_tenants["doc_b"]

    await seed_chunks(
        [
            Chunk(
                tenant_id=tenant_b,
                document_id=doc_b,
                chunk_index=0,
                content="b-perfect-match",
                embedding=_unit_vector(0),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            ),
            Chunk(
                tenant_id=tenant_a,
                document_id=doc_a,
                chunk_index=0,
                content="a-orthogonal",
                embedding=_unit_vector(1),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            ),
        ]
    )

    async with tenant_session(app_sessionmaker, tenant_a) as session:
        results = await ChunkRepository(session).search(_unit_vector(0), k=5)

    contents = {c.content for c in results}
    assert "a-orthogonal" in contents
    assert "b-perfect-match" not in contents
