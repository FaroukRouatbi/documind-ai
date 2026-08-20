import structlog
import uuid

import pybreaker

from app.core.database import get_worker_session
from app.documents.repository import DocumentRepository
from app.documents.s3 import S3Client
from app.ingestion.base import IngestionStrategy
from app.chunks.repository import ChunkRepository
from app.core.metrics import ingestion_metrics

logger = structlog.get_logger()

async def process_upload(
        bucket: str,
        s3_key: str,
        *,
        s3_client: S3Client,
        strategy: IngestionStrategy,
) -> None:
    tenant_id = uuid.UUID(s3_key.split("/")[0])

    async with get_worker_session(tenant_id) as session:
        doc_repo = DocumentRepository(session)
        document = await doc_repo.get_by_s3_key(s3_key)

        if document is None:
            logger.warning("orphan_upload", s3_key=s3_key, tenant_id=str(tenant_id))
            async with ingestion_metrics(strategy="text", correlation_id=None) as m:
                m.orphan()
            return

        structlog.contextvars.bind_contextvars(correlation_id=document.correlation_id)

        async with ingestion_metrics(strategy="text", correlation_id=document.correlation_id) as m:
            try:
                await doc_repo.update_status(document.id, "processing")
                file_bytes = await s3_client.download(bucket, s3_key)
                chunks = await strategy.process(document, file_bytes)

                chunk_repo = ChunkRepository(session)
                await chunk_repo.bulk_create(
                    chunks,
                    document=document,
                    ingestion_strategy="text",
                )

                await doc_repo.update_status(document.id, "ready")
                m.success(len(chunks))

            except pybreaker.CircuitBreakerError:
                logger.warning("service_down_retry", s3_key=s3_key)
                m.service_down()
                raise

            except Exception:
                logger.exception("ingestion_failed", s3_key=s3_key)
                m.failure()
                async with get_worker_session(tenant_id) as fail_session:
                    await DocumentRepository(fail_session).update_status(document.id, "failed")
                return