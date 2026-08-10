import json
import asyncio

import boto3
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception
from botocore.exceptions import ClientError

TRANSIENT_ERROR_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "InternalServerException",
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
    ):
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id
        self._dimensions = dimensions
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=30,
            exclude=[_is_permanent],
        )

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_guarded, text)

    def _embed_guarded(self, text: str) -> list[float]:
        return self._breaker.call(self._embed_with_retry, text)

    @retry(
        retry=retry_if_exception(_is_transient),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
    )
    def _embed_with_retry(self, text: str) -> list[float]:
        return self._embed_sync(text)

    def _embed_sync(self, text: str) -> list[float]:
        body = json.dumps({
            "inputText": text,
            "dimensions": self._dimensions,
            "normalize": True,
        })
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        payload = json.loads(response["body"].read())
        return payload["embedding"]

if __name__ == "__main__":
    def make_error(code):
        return ClientError({"Error": {"Code": code, "Message": "x"}}, "InvokeModel")

    print(_is_transient(make_error("ThrottlingException")))  # True
    print(_is_transient(make_error("ValidationException")))  # False
    print(_is_permanent(make_error("ValidationException")))  # True

    # breaker trip test
    br = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, exclude=[_is_permanent])
    def always_throttle():
        raise make_error("ThrottlingException")
    for i in range(5):
        try:
            br.call(always_throttle)
        except pybreaker.CircuitBreakerError:
            print(f"attempt {i}: breaker OPEN (fast-fail)")
        except ClientError:
            print(f"attempt {i}: passed through, counted as failure")