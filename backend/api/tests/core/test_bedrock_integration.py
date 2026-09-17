import pytest

from app.core.bedrock import BedrockEmbeddingClient


@pytest.mark.integration
async def test_embed_returns_real_vector_from_bedrock():
    client = BedrockEmbeddingClient("us-east-1")

    vector = await client.embed("Revenue grew significantly this quarter.")

    assert len(vector) == 1024
    assert any(v != 0.0 for v in vector)
