from app.chunks.models import Chunk
from app.chunks.repository import ChunkRepository
from app.retrieval.service import RetrievalService
from tests.conftest import tenant_session


def _unit_vector(dim, size=1024):
    vec = [0.0] * size
    vec[dim] = 1.0
    return vec


class _FakeEmbedder:
    model_id = "test"
    embedding_version = "v1"

    def __init__(self, vector):
        self._vector = vector

    async def embed(self, text: str) -> list[float]:
        return self._vector


async def test_retrieve_embeds_searches_and_orders(app_sessionmaker, seeded_tenants, seed_chunks):
    tenant_a = seeded_tenants["tenant_a"]
    doc_a = seeded_tenants["doc_a"]

    await seed_chunks(
        [
            Chunk(
                tenant_id=tenant_a,
                document_id=doc_a,
                chunk_index=i,
                content=f"chunk-{i}",
                embedding=_unit_vector(i),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            )
            for i in range(3)
        ]
    )

    # Fake embedder turns the query into the axis-0 vector → chunk-0 is the best match
    embedder = _FakeEmbedder(_unit_vector(0))

    async with tenant_session(app_sessionmaker, tenant_a) as session:
        service = RetrievalService(embedder, ChunkRepository(session))
        results = await service.retrieve("any query text", k=3)

    contents = [c.content for c in results]
    assert set(contents) == {"chunk-0", "chunk-1", "chunk-2"}  # all retrieved, tenant-scoped
    assert "chunk-0" in contents  # the best match is present


async def test_retrieve_dedups_identical_content(app_sessionmaker, seeded_tenants, seed_chunks):
    tenant_a = seeded_tenants["tenant_a"]
    doc_a = seeded_tenants["doc_a"]

    await seed_chunks(
        [
            Chunk(
                tenant_id=tenant_a,
                document_id=doc_a,
                chunk_index=0,
                content="duplicate",
                embedding=_unit_vector(0),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            ),
            Chunk(
                tenant_id=tenant_a,
                document_id=doc_a,
                chunk_index=1,
                content="duplicate",
                embedding=_unit_vector(1),
                embedding_model="test",
                embedding_version="v1",
                ingestion_strategy="text",
            ),
        ]
    )

    embedder = _FakeEmbedder(_unit_vector(0))
    async with tenant_session(app_sessionmaker, tenant_a) as session:
        service = RetrievalService(embedder, ChunkRepository(session))
        results = await service.retrieve("q", k=5)

    contents = [c.content for c in results]
    assert contents.count("duplicate") == 1  # dedup collapsed the two identical-content chunks
