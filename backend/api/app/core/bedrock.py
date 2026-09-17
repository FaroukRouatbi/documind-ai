import asyncio
import json

import boto3
import pybreaker
from botocore.config import Config
from botocore.exceptions import ClientError

TRANSIENT_ERROR_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "InternalServerException",
    "ModelNotReadyException",
}


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, ClientError):
        return exc.response["Error"]["Code"] in TRANSIENT_ERROR_CODES
    return False


def _is_permanent(exc: Exception) -> bool:
    return not _is_transient(exc)


class BedrockEmbeddingClient:
    def __init__(
        self,
        region: str,
        model_id: str = "amazon.titan-embed-text-v2:0",
        dimensions: int = 1024,
        embedding_version: str = "1",
    ):
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(retries={"max_attempts": 4, "mode": "standard"}),
        )
        self._model_id = model_id
        self._dimensions = dimensions
        self._embedding_version = embedding_version
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=30,
            exclude=[_is_permanent],
        )

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_guarded, text)

    def _embed_guarded(self, text: str) -> list[float]:
        return self._breaker.call(self._embed_sync, text)

    def _embed_sync(self, text: str) -> list[float]:
        body = json.dumps(
            {
                "inputText": text,
                "dimensions": self._dimensions,
                "normalize": True,
            }
        )
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        payload = json.loads(response["body"].read())
        return payload["embedding"]

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def embedding_version(self) -> str:
        return self._embedding_version
