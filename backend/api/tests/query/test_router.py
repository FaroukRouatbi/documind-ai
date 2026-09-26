from app.chunks.models import Chunk
from app.core.config import settings
from app.generation.prompts import NO_ANSWER_RESPONSE
from tests.conftest import unit_vector


def _chunk_for(tenant_id, document_id, content, embedding):
    return Chunk(
        tenant_id=tenant_id,
        document_id=document_id,
        chunk_index=0,
        content=content,
        embedding=embedding,
        embedding_model="test",
        embedding_version="v1",
        ingestion_strategy="text",
    )


async def test_query_returns_answer_with_resolved_citation(
    client, fake_generation, seeded_tenants, seed_chunks
):
    chunk = _chunk_for(
        seeded_tenants["tenant_a"],
        seeded_tenants["doc_a"],
        "Revenue grew 18%.",
        unit_vector(0),
    )
    await seed_chunks([chunk])
    fake_generation.text = "Revenue grew 18% [1]."

    response = await client.post("/v1/query", json={"query": "How did revenue do?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Revenue grew 18% [1]."
    assert body["truncated"] is False
    assert body["query_id"]
    assert len(body["citations"]) == 1
    citation = body["citations"][0]
    assert citation["chunk_id"] == str(chunk.id)
    assert citation["filename"] == "a.md"
    assert citation["content"] == "Revenue grew 18%."
    assert body["blocked"] is False


async def test_query_with_no_matching_chunks_skips_generation(client, fake_generation):
    response = await client.post("/v1/query", json={"query": "How did revenue do?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == NO_ANSWER_RESPONSE
    assert body["citations"] == []
    assert fake_generation.calls == 0


async def test_query_never_sees_another_tenants_chunks(
    client, fake_generation, seeded_tenants, seed_chunks
):
    await seed_chunks(
        [
            _chunk_for(
                seeded_tenants["tenant_b"],
                seeded_tenants["doc_b"],
                "Tenant B's confidential revenue figure.",
                unit_vector(0),
            )
        ]
    )

    response = await client.post("/v1/query", json={"query": "What is the revenue?"})

    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == []
    assert fake_generation.calls == 0


async def test_query_drops_citations_to_nonexistent_documents(
    client, fake_generation, seeded_tenants, seed_chunks
):
    await seed_chunks(
        [
            _chunk_for(
                seeded_tenants["tenant_a"],
                seeded_tenants["doc_a"],
                "Revenue grew 18%.",
                unit_vector(0),
            )
        ]
    )
    fake_generation.text = "Revenue grew [1][7]."

    response = await client.post("/v1/query", json={"query": "revenue?"})

    assert response.status_code == 200
    assert len(response.json()["citations"]) == 1


async def test_query_flags_answer_truncated_by_token_limit(
    client, fake_generation, seeded_tenants, seed_chunks
):
    await seed_chunks(
        [
            _chunk_for(
                seeded_tenants["tenant_a"],
                seeded_tenants["doc_a"],
                "Revenue grew 18%.",
                unit_vector(0),
            )
        ]
    )

    fake_generation.text = "Revenue grew [1]"
    fake_generation.stop_reason = "max_tokens"

    response = await client.post("/v1/query", json={"query": "revenue?"})

    assert response.status_code == 200
    assert response.json()["truncated"] is True


async def test_query_rejects_invalid_input(client, fake_generation):
    empty = await client.post("/v1/query", json={"query": ""})
    too_many = await client.post("/v1/query", json={"query": "x", "k": 100})

    assert empty.status_code == 422
    assert too_many.status_code == 422


async def test_query_flags_blocked_answer_when_guardrail_intervenes(
    client, fake_generation, seeded_tenants, seed_chunks
):
    await seed_chunks(
        [
            _chunk_for(
                seeded_tenants["tenant_a"],
                seeded_tenants["doc_a"],
                "Revenue grew 18%.",
                unit_vector(0),
            )
        ]
    )

    fake_generation.text = "This request was blocked by content policy"
    fake_generation.guardrail_intervened = True

    response = await client.post("/v1/query", json={"query": "revenue?"})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked"] is True
    assert body["citations"] == []


async def test_query_returns_429_when_rate_limited(
    client, fake_generation, app_with_redis, monkeypatch
):
    monkeypatch.setattr(settings, "query_rate_limit_per_minute", 2)

    for _ in range(2):
        allowed = await client.post("/v1/query", json={"query": "hi"})
        assert allowed.status_code == 200

    limited = await client.post("/v1/query", json={"query": "hi"})

    assert limited.status_code == 429
    assert limited.headers["Retry-After"] == "60"
