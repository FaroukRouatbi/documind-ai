import structlog

from app.chunks.models import Chunk
from app.generation.client import Generator
from app.generation.prompts import build_prompt, extract_citations
from app.generation.schemas import AnswerResult

logger = structlog.get_logger()


class GenerationService:
    def __init__(self, client: Generator):
        self._client = client

    async def generate_answer(self, query: str, chunks: list[Chunk]) -> AnswerResult:
        prompt = build_prompt(query, chunks)
        result = await self._client.generate(prompt.system, prompt.user_content)

        cited = extract_citations(result.text)
        invalid = [i for i in cited if i not in prompt.citation_map]
        if invalid:
            logger.warning(
                "invalid_citations", indices=invalid, documents_provided=len(prompt.citation_map)
            )

        if result.stop_reason == "max_tokens":
            logger.warning("generation_truncated", output_tokens=result.output_tokens)

        if result.guardrail_intervened:
            logger.warning("guardrail_intervened")

        return AnswerResult(
            text=result.text,
            citations=[prompt.citation_map[i] for i in cited if i in prompt.citation_map],
            stop_reason=result.stop_reason,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            guardrail_intervened=result.guardrail_intervened,
        )
