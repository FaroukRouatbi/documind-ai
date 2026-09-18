import pytest

from app.generation.client import BedrockGenerationClient


@pytest.mark.integration
async def test_generate_returns_text_from_claude():
    client = BedrockGenerationClient("us-east-1")

    result = await client.generate("Reply with exactly the word: pong")

    assert result.text.strip()
    assert result.stop_reason == "end_turn"
    assert result.input_tokens > 0
    assert result.output_tokens > 0
