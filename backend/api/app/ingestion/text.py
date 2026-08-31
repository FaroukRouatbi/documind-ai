import asyncio
from dataclasses import replace

from app.core.embedder import Embedder
from app.documents.models import Document
from app.ingestion.base import IngestionStrategy
from app.ingestion.chunking import chunk_document
from app.ingestion.schemas import ChunkData


class TextIngestionStrategy(IngestionStrategy):
    def __init__(self, embedder: Embedder, max_concurrency: int = 8):
        self._embedder = embedder
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def process(self, document: Document, file_bytes: bytes) -> list[ChunkData]:
        markdown = file_bytes.decode("utf-8")

        chunks = chunk_document(
            markdown,
            embedding_model=self._embedder.model_id,
            embedding_version=self._embedder.embedding_version,
        )

        embedded = await asyncio.gather(*(self._embed_chunk(chunk) for chunk in chunks))

        return list(embedded)

    async def _embed_chunk(self, chunk: ChunkData) -> ChunkData:
        async with self._semaphore:
            vector = await self._embedder.embed(chunk.content)
        return replace(chunk, embedding=vector)


if __name__ == "__main__":
    import asyncio

    from app.documents.models import Document

    class FakeEmbedder:
        model_id = "fake-model"
        embedding_version = "1"

        async def embed(self, text: str) -> list[float]:
            return [0.0] * 1024

    async def main():
        strategy = TextIngestionStrategy(FakeEmbedder())
        sample = "# Title\n\nSome content here.\n\n## Section\n\nMore content."
        chunks = await strategy.process(Document(), sample.encode("utf-8"))
        for c in chunks:
            print(
                f"[{c.chunk_index}] path={c.heading_path!r} embedded={c.embedding is not None} model={c.embedding_model}"  # noqa: E501
            )

    asyncio.run(main())
