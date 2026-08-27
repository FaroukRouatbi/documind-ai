import asyncio

import boto3
import pybreaker
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


def generate_upload_post(s3_key: str, content_type: str, max_size_bytes: int = 50_000_000) -> dict:
    client = boto3.client(
        "s3", region_name=settings.aws_region, config=Config(signature_version="s3v4")
    )
    return client.generate_presigned_post(
        Bucket=settings.documents_bucket_name,
        Key=s3_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 0, max_size_bytes],
        ],
        ExpiresIn=300,
    )


S3_TRANSIENT_ERROR_CODES = {
    "SlowDown",
    "InternalError",
    "ServiceUnavailable",
    "RequestTimeout",
    "RequestTimeoutException",
    "PriorRequestNotComplete",
}


def _is_transient_s3(exc: Exception) -> bool:
    if isinstance(exc, ClientError):
        return exc.response["Error"]["Code"] in S3_TRANSIENT_ERROR_CODES
    return False


def _is_permanent_s3(exc: Exception) -> bool:
    return not _is_transient_s3(exc)


class S3Client:
    def __init__(self, region: str):
        self._client = boto3.client(
            "s3",
            region_name=region,
            config=Config(retries={"max_attempts": 4, "mode": "standard"}),
        )
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=30,
            exclude=[_is_permanent_s3],
        )

    async def download(self, bucket: str, key: str) -> bytes:
        return await asyncio.to_thread(self._download_guarded, bucket, key)

    def _download_guarded(self, bucket: str, key: str) -> bytes:
        return self._breaker.call(self._download_sync, bucket, key)

    def _download_sync(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


if __name__ == "__main__":

    def make_error(code):
        return ClientError({"Error": {"Code": code, "Message": "x"}}, "GetObject")

    print(_is_transient_s3(make_error("SlowDown")))  # True
    print(_is_transient_s3(make_error("NoSuchKey")))  # False
    print(_is_permanent_s3(make_error("NoSuchKey")))  # True
