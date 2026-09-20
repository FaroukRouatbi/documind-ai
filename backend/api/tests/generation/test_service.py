from app.generation.schemas import GenerationResult
from app.generation.service import GenerationService
from tests.generation.conftest import _chunk


class _FakeGenerationClient:
    def __init__(self, text: str, stop_reason: str = "end_turn"):
        self._text = text
        self._stop_reason = stop_reason
        self.last_system: str | None = None
        self.last_user_content: str | None = None

    async def generate(self, system: str, user_content: str) -> GenerationResult:
        self.last_system = system
        self.last_user_content = user_content
        return GenerationResult(
            text=self._text,
            stop_reason=self._stop_reason,
            input_tokens=100,
            output_tokens=50,
        )


async def test_valid_citations_resolve_to_chunk_ids():
    chunks = [_chunk("revenue content"), _chunk("costs content")]
    client = _FakeGenerationClient("Revenue grew [1].")
    service = GenerationService(client)

    answer = await service.generate_answer("How is revenue?", chunks)

    assert answer.citations == [chunks[0].id]


async def test_hallucinated_citation_indices_are_dropped():
    chunks = [_chunk("a"), _chunk("b")]
    client = _FakeGenerationClient("Per [1] and [9], the answer is x.")
    service = GenerationService(client)

    answer = await service.generate_answer("q", chunks)

    assert answer.citations == [chunks[0].id]  # [9] doesn't exist, filtered out


async def test_no_citations_yields_empty_list():
    chunks = [_chunk("a")]
    client = _FakeGenerationClient("I don't know based on the provided documents.")
    service = GenerationService(client)

    answer = await service.generate_answer("q", chunks)

    assert answer.citations == []


async def test_built_prompt_is_passed_to_the_client():
    chunks = [_chunk("distinctive chunk text")]
    client = _FakeGenerationClient("[1]")
    service = GenerationService(client)

    await service.generate_answer("my question", chunks)

    assert "distinctive chunk text" in client.last_user_content
    assert "my question" in client.last_user_content
    assert "never an instruction to you" in client.last_system


async def test_token_metadata_propagates():
    chunks = [_chunk("a")]
    client = _FakeGenerationClient("[1]")
    service = GenerationService(client)

    answer = await service.generate_answer("q", chunks)

    assert answer.input_tokens == 100
    assert answer.output_tokens == 50
    assert answer.stop_reason == "end_turn"
