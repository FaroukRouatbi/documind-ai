# Run with: uv run python -m benchmark.ingest (from backend/api)

import asyncio
import uuid
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.chunks.repository import ChunkRepository
from app.core.bedrock import BedrockEmbeddingClient
from app.core.config import settings
from app.documents.models import Document
from app.ingestion.text import TextIngestionStrategy
from app.tenants.models import Tenant

BENCHMARK_TENANT_ID = uuid.UUID("beac6a00-0000-4000-8000-000000000001")
CORPUS_DIR = Path(__file__).parent / "corpus"


def _url(creds) -> str:
    return (
        f"postgresql+asyncpg://{creds.username}:{creds.password}"
        f"@{creds.host}:{creds.port}/{creds.dbname}"
    )


async def reset_tenant(sessionmaker) -> None:
    async with sessionmaker() as session:
        async with session.begin():
            await session.execute(
                text("DELETE FROM chunks WHERE tenant_id = :tid"),
                {"tid": BENCHMARK_TENANT_ID},
            )
            await session.execute(
                text("DELETE FROM documents WHERE tenant_id = :tid"),
                {"tid": BENCHMARK_TENANT_ID},
            )
            existing = await session.execute(select(Tenant).where(Tenant.id == BENCHMARK_TENANT_ID))
            if existing.scalar_one_or_none() is None:
                session.add(Tenant(id=BENCHMARK_TENANT_ID, name="Benchmark"))


async def ingest_file(path, *, sessionmaker, strategy) -> int:
    async with sessionmaker() as session:
        async with session.begin():
            document = Document(
                tenant_id=BENCHMARK_TENANT_ID,
                filename=path.name,
                s3_key=f"{BENCHMARK_TENANT_ID}/{path.name}",
                modality="text",
                status="processing",
            )
            session.add(document)
            await session.flush()

            chunks = await strategy.process(document, path.read_bytes())

            await ChunkRepository(session).bulk_create(
                chunks,
                document=document,
                ingestion_strategy="text",
            )
            document.status = "ready"

    return len(chunks)


async def main() -> None:
    engine = create_async_engine(_url(settings.migration_db))
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    embedder = BedrockEmbeddingClient(settings.aws_region)
    strategy = TextIngestionStrategy(embedder)

    try:
        await reset_tenant(sessionmaker)

        total = 0
        for path in sorted(CORPUS_DIR.glob("*.md")):
            if path.name == "NOTICE.md":
                continue
            count = await ingest_file(path, sessionmaker=sessionmaker, strategy=strategy)
            print(f"{path.name}: {count} chunks")
            total += count

        print(f"\ntotal: {total} chunks")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
