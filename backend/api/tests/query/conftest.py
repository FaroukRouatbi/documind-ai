import pytest_asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunks.repository import ChunkRepository
from app.core.database import get_tenant_db
from app.generation.schemas import GenerationResult
from app.generation.service import GenerationService
from app.main import app
from app.query.dependencies import get_generation_service, get_retrieval_service
from app.retrieval.service import RetrievalService
from tests.conftest import unit_vector


class FakeEmbedder:
    model_id = "test"
    embedding_version = "v1"

    async def embed(self, text: str) -> list[float]:
        return unit_vector(0)


class FakeGenerationClient:
    def __init__(self):
        self.text = "No answer set."
        self.stop_reason = "end_turn"
        self.guardrail_intervened = False
        self.calls = 0

    async def generate(self, system: str, user_content: str) -> GenerationResult:
        self.calls += 1
        return GenerationResult(
            text=self.text,
            stop_reason=self.stop_reason,
            input_tokens=100,
            output_tokens=50,
            guardrail_intervened=self.guardrail_intervened,
        )


@pytest_asyncio.fixture
async def fake_generation(as_tenant_a):
    generation_client = FakeGenerationClient()

    def _retrieval(session: AsyncSession = Depends(get_tenant_db)) -> RetrievalService:
        return RetrievalService(FakeEmbedder(), ChunkRepository(session))

    def _generation() -> GenerationService:
        return GenerationService(generation_client)

    app.dependency_overrides[get_retrieval_service] = _retrieval
    app.dependency_overrides[get_generation_service] = _generation
    yield generation_client
    app.dependency_overrides.pop(get_retrieval_service, None)
    app.dependency_overrides.pop(get_generation_service, None)
