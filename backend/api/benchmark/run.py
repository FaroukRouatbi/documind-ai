"""Run the retrieval benchmark.

Run with: uv run python -m benchmark.run   (from backend/api)
"""

import asyncio
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.chunks.models import Chunk
from app.chunks.repository import ChunkRepository
from app.core.bedrock import BedrockEmbeddingClient
from app.core.config import settings
from app.retrieval.assembly import dedup_chunks
from benchmark.ingest import BENCHMARK_TENANT_ID, _url

QUESTIONS_PATH = Path(__file__).parent / "questions.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"
RETRIEVE_K = 10
RECALL_AT = (1, 3, 5, 10)


def load_questions() -> list[dict]:
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "unknown"


async def retrieve(session, embedder, query: str) -> tuple[list[Chunk], dict]:
    t0 = time.perf_counter()
    vector = await embedder.embed(query)
    t1 = time.perf_counter()
    chunks = await ChunkRepository(session).search(vector, k=RETRIEVE_K)
    t2 = time.perf_counter()
    deduped = dedup_chunks(chunks, key=lambda c: c.content)
    t3 = time.perf_counter()
    timings = {
        "embed_ms": round((t1 - t0) * 1000, 1),
        "search_ms": round((t2 - t1) * 1000, 1),
        "dedup_ms": round((t3 - t2) * 1000, 1),
        "total_ms": round((t3 - t0) * 1000, 1),
    }
    return deduped, timings


def first_hit_rank(chunks: list[Chunk], expected: list[str]) -> int | None:
    for rank, chunk in enumerate(chunks, start=1):
        if any(substring in chunk.content for substring in expected):
            return rank
    return None


async def main() -> None:
    engine = create_async_engine(_url(settings.db))
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    embedder = BedrockEmbeddingClient(settings.aws_region)

    questions = load_questions()
    answerable: list[dict] = []
    unanswerable: list[dict] = []

    try:
        async with sessionmaker() as session:
            async with session.begin():
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tid, true)"),
                    {"tid": str(BENCHMARK_TENANT_ID)},
                )

                for q in questions:
                    chunks, timings = await retrieve(session, embedder, q["question"])
                    retrieved = [
                        {"heading": c.heading_path, "preview": c.content[:80]} for c in chunks
                    ]

                    if not q["expected_chunks"]:
                        unanswerable.append(
                            {
                                "id": q["id"],
                                "question": q["question"],
                                "retrieved": retrieved,
                                "timings": timings,
                            }
                        )
                        continue

                    rank = first_hit_rank(chunks, q["expected_chunks"])
                    answerable.append(
                        {
                            "id": q["id"],
                            "question": q["question"],
                            "expected_heading": q["expected_heading"],
                            "rank": rank,
                            "retrieved": retrieved,
                            "timings": timings,
                        }
                    )
    finally:
        await engine.dispose()

    total = len(answerable)
    mrr = sum(1 / r["rank"] for r in answerable if r["rank"]) / total
    recall = {
        f"recall@{k}": sum(1 for r in answerable if r["rank"] and r["rank"] <= k) / total
        for k in RECALL_AT
    }

    all_results = answerable + unanswerable
    totals = sorted(r["timings"]["total_ms"] for r in all_results)
    p95 = totals[min(int(len(totals) * 0.95), len(totals) - 1)]

    latency = {
        "avg_ms": round(sum(totals) / len(totals), 1),
        "p50_ms": round(median(totals), 1),
        "p95_ms": round(p95, 1),
        "embed_avg_ms": round(
            sum(r["timings"]["embed_ms"] for r in all_results) / len(all_results), 1
        ),
        "search_avg_ms": round(
            sum(r["timings"]["search_ms"] for r in all_results) / len(all_results), 1
        ),
    }

    metrics = {
        "questions": total,
        "mrr": round(mrr, 4),
        **{k: round(v, 4) for k, v in recall.items()},
        "latency": latency,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / f"{stamp}.json"
    path.write_text(
        json.dumps(
            {
                "timestamp": stamp,
                "git_sha": git_sha(),
                "retrieve_k": RETRIEVE_K,
                "metrics": metrics,
                "answerable": answerable,
                "unanswerable": unanswerable,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"questions: {total}")
    print(f"MRR:       {metrics['mrr']}")
    for k in RECALL_AT:
        print(f"recall@{k}:  {metrics[f'recall@{k}']}")
    print(
        f"\nlatency:   avg {latency['avg_ms']}ms  p50 {latency['p50_ms']}ms"
        f"  p95 {latency['p95_ms']}ms"
    )
    print(f"           embed {latency['embed_avg_ms']}ms  search {latency['search_avg_ms']}ms")
    print(f"\nmisses: {[r['id'] for r in answerable if r['rank'] is None]}")
    print(f"written: {path}")


if __name__ == "__main__":
    asyncio.run(main())
