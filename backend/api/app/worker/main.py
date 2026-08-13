import asyncio
import json
import logging
import urllib.parse

import boto3
import pybreaker

from app.documents.s3 import S3Client
from app.core.config import settings
from app.core.bedrock import BedrockEmbeddingClient
from app.ingestion.text import TextIngestionStrategy
from app.worker.processor import process_upload


logger = logging.getLogger(__name__)

async def handle_message(message, *, s3_client, strategy) -> None:
    body = json.loads(message["Body"])

    if "Records" not in body:
        logger.info("s3_test_event_skipped")
        return

    for record in body["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        await process_upload(bucket, key, s3_client=s3_client, strategy=strategy)

async def run() -> None:
    s3_client = S3Client(settings.aws_region)
    embedder = BedrockEmbeddingClient(settings.aws_region)
    strategy = TextIngestionStrategy(embedder)
    sqs = boto3.client("sqs", region_name=settings.aws_region)

    logger.info("worker_started")

    while True:
        try:
            response = await asyncio.to_thread(
                sqs.receive_message,
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
        except Exception:
            logger.exception("sqs_receive_failed")
            await asyncio.sleep(5)
            continue

        messages = response.get("Messages", [])

        for message in messages:
            try:
                await handle_message(message, s3_client=s3_client, strategy=strategy)
            except pybreaker.CircuitBreakerError:
                logger.warning("service_down_leaving_message")
                continue
            except Exception:
                logger.exception("message_handling_failed")
                continue
            else:
                await asyncio.to_thread(
                    sqs.delete_message,
                    QueueUrl=settings.sqs_queue_url,
                    ReceiptHandle=message["ReceiptHandle"],
                )

if __name__ == "__main__":
    asyncio.run(run())