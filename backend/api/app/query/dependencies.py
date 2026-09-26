from functools import lru_cache

import redis
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunks.repository import ChunkRepository
from app.core.bedrock import BedrockEmbeddingClient
from app.core.config import settings
from app.core.database import get_tenant_db
from app.core.rate_limit import check_rate_limit
from app.core.security import get_current_user
from app.generation.client import BedrockGenerationClient
from app.generation.service import GenerationService
from app.retrieval.service import RetrievalService


@lru_cache
def get_embedder() -> BedrockEmbeddingClient:
    return BedrockEmbeddingClient(settings.aws_region)


@lru_cache
def get_generation_client() -> BedrockGenerationClient:
    return BedrockGenerationClient(
        settings.aws_region,
        guardrail_arn=settings.bedrock_guardrail_arn,
        guardrail_version=settings.bedrock_guardrail_version,
    )


def get_retrieval_service(
    session: AsyncSession = Depends(get_tenant_db),
) -> RetrievalService:
    return RetrievalService(get_embedder(), ChunkRepository(session))


def get_generation_service() -> GenerationService:
    return GenerationService(get_generation_client())


def get_redis(request: Request) -> redis.Redis | None:
    return request.app.state.redis


async def enforce_rate_limit(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> None:
    redis_client = getattr(request.app.state, "redis", None)

    allowed = await check_rate_limit(
        redis_client, current_user["tenant_id"], settings.query_rate_limit_per_minute
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Query rate limit exceeded. Try again shortly.",
            headers={"Retry-After": "60"},
        )
