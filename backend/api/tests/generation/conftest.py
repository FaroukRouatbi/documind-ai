import uuid

from app.chunks.models import Chunk


def _chunk(content: str) -> Chunk:
    return Chunk(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=0,
        content=content,
        embedding_model="test",
        embedding_version="v1",
        ingestion_strategy="text",
    )
