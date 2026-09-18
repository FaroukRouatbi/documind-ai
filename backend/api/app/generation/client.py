import asyncio
import json

import boto3
import pybreaker
from botocore.config import Config

from app.core.bedrock_errors import is_permanent
from app.generation.schemas import GenerationResult


class BedrockGenerationClient:
    def __init__(
        self,
        region: str,
        model_id: str = "global.anthropic.claude-sonnet-4-6",
        max_tokens: int = 1024,
    ):
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(retries={"max_attempts": 4, "mode": "standard"}),
        )
        self._model_id = model_id
        self._max_tokens = max_tokens
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=30, exclude=[is_permanent]
        )

    async def generate(self, system: str, user_content: str) -> GenerationResult:
        return await asyncio.to_thread(self._generate_guarded, system, user_content)

    def _generate_guarded(self, system: str, user_content: str) -> GenerationResult:
        return self._breaker.call(self._generate_sync, system, user_content)

    def _generate_sync(self, system: str, user_content: str) -> GenerationResult:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self._max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user_content}],
            }
        )
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        payload = json.loads(response["body"].read())
        return GenerationResult(
            text=payload["content"][0]["text"],
            stop_reason=payload["stop_reason"],
            input_tokens=payload["usage"]["input_tokens"],
            output_tokens=payload["usage"]["output_tokens"],
        )
