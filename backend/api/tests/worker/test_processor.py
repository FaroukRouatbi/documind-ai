from sqlalchemy import select

from app.chunks.models import Chunk
from app.documents.repository import DocumentRepository
from app.ingestion.base import IngestionStrategy
from app.ingestion.schemas import ChunkData
from app.worker.processor import process_upload
from tests.conftest import tenant_session


class _FakeS3Client:
    def __init__(self, content: bytes):
        self._content = content

    async def download(self, bucket: str, key: str) -> bytes:
        return self._content


class _FakeStrategy(IngestionStrategy):
    def __init__(self):
        self.process_calls = 0

    async def process(self, document, file_bytes: bytes) -> list[ChunkData]:
        self.process_calls += 1
        return [
            ChunkData(
                content="chunk-1",
                chunk_index=0,
                embedding=[0.0] * 1024,
                embedding_model="test",
                embedding_version="v1",
                heading_path=None,
                token_count=5,
                parent_index=None,
            )
        ]


async def test_second_ingestion_of_same_content_is_skipped(
    app_sessionmaker, seeded_tenants, cleanup_chunks
):
    tenant_a = seeded_tenants["tenant_a"]
    doc_a_s3_key = seeded_tenants["doc_a_s3_key"]

    content = b"# Title\n\nSome content."
    s3_client = _FakeS3Client(content)
    strategy = _FakeStrategy()

    # first run — ingests
    await process_upload("bucket", doc_a_s3_key, s3_client=s3_client, strategy=strategy)

    # second run — same content, should short-circuit
    await process_upload("bucket", doc_a_s3_key, s3_client=s3_client, strategy=strategy)

    assert strategy.process_calls == 1  # expensive path ran exactly once

    # and only one set of chunks exists
    async with tenant_session(app_sessionmaker, tenant_a) as session:
        result = await session.execute(select(Chunk))
        chunks = result.scalars().all()
    assert len(chunks) == 1

    # confirm the first run actually completed (otherwise the skip can't happen)
    async with tenant_session(app_sessionmaker, tenant_a) as session:
        doc = await DocumentRepository(session).get_by_id(seeded_tenants["doc_a"])
    assert doc is not None
    assert doc.status == "ready"


async def test_changed_content_is_reprocessed(app_sessionmaker, seeded_tenants, cleanup_chunks):
    doc_a_s3_key = seeded_tenants["doc_a_s3_key"]
    strategy = _FakeStrategy()

    await process_upload(
        "bucket",
        doc_a_s3_key,
        s3_client=_FakeS3Client(b"original content"),
        strategy=strategy,
    )

    await process_upload(
        "bucket",
        doc_a_s3_key,
        s3_client=_FakeS3Client(b"DIFFERENT content"),
        strategy=strategy,
    )

    assert strategy.process_calls == 2  # different hash → re-processed
