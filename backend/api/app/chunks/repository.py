from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunks.models import Chunk
from app.documents.models import Document
from app.ingestion.schemas import ChunkData


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(
        self,
        chunks: list[ChunkData],
        *,
        document: Document,
        ingestion_strategy: str,
    ) -> list[Chunk]:
        orm_chunks = [
            Chunk(
                tenant_id=document.tenant_id,
                document_id=document.id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding=c.embedding,
                embedding_model=c.embedding_model,
                embedding_version=c.embedding_version,
                heading_path=c.heading_path,
                ingestion_strategy=ingestion_strategy,
                token_count=c.token_count,
                parent_chunk_id=None,
            )
            for c in chunks
        ]

        self.session.add_all(orm_chunks)
        await self.session.flush()

        for orm_chunk, data in zip(orm_chunks, chunks, strict=True):
            if data.parent_index is not None:
                orm_chunk.parent_chunk_id = orm_chunks[data.parent_index].id

        await self.session.flush()

        return orm_chunks

    async def search(self, query_emebdding: list[float], k: int = 5) -> list[Chunk]:
        await self.session.execute(text("SET LOCAL hnsw.iterative_scan = strict_order"))

        result = await self.session.execute(
            select(Chunk).order_by(Chunk.embedding.cosine_distance(query_emebdding)).limit(k)
        )
        return list(result.scalars().all())
