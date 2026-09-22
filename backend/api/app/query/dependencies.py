from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunks.repository import ChunkRepository
from app.core.bedrock import BedrockEmbeddingClient
from app.core.config import settings
from app.core.database import get_tenant_db
from app.generation.client import BedrockGenerationClient
from app.generation.service import GenerationService
from app.retrieval.service import RetrievalService


@lru_cache
def get_embedder() -> BedrockEmbeddingClient:
    return BedrockEmbeddingClient(settings.aws_region)


@lru_cache
def get_generation_client() -> BedrockGenerationClient:
    return BedrockGenerationClient(settings.aws_region)


def get_retrieval_service(
    session: AsyncSession = Depends(get_tenant_db),
) -> RetrievalService:
    return RetrievalService(get_embedder(), ChunkRepository(session))


def get_generation_service() -> GenerationService:
    return GenerationService(get_generation_client())
