from app.chunks.models import Chunk
from app.chunks.repository import ChunkRepository
from app.core.embedder import Embedder
from app.retrieval.assembly import dedup_chunks, reorder_lost_in_middle


class RetrievalService:
    def __init__(self, embedder: Embedder, repository: ChunkRepository):
        self._embedder = embedder
        self._repository = repository

    async def retrieve(self, query: str, k: int = 5) -> list[Chunk]:
        query_vector = await self._embedder.embed(query)
        chunks = await self._repository.search(query_vector, k)
        deduped = dedup_chunks(chunks, key=lambda c: c.content)
        return reorder_lost_in_middle(deduped)
