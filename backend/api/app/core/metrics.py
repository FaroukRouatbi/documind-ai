import time

from aws_embedded_metrics.logger.metrics_logger import MetricsLogger
from aws_embedded_metrics.logger.metrics_logger_factory import create_metrics_logger


class IngestionMetrics:
    def __init__(self, *, strategy: str, correlation_id: str | None):
        self._strategy = strategy
        self._correlation_id = correlation_id
        self._logger: MetricsLogger | None = None
        self._start: float | None = None

    async def __aenter__(self) -> IngestionMetrics:
        self._logger = create_metrics_logger()
        self._logger.set_namespace("DocuMind/Ingestion")
        self._logger.set_dimensions({"Strategy": self._strategy})
        if self._correlation_id is not None:
            self._logger.set_property("correlation_id", self._correlation_id)
        self._start = time.monotonic()
        return self

    def success(self, chunk_count: int) -> None:
        assert self._logger is not None
        self._logger.put_metric("DocsProcessed", 1, "Count")
        self._logger.put_metric("ChunksCreated", chunk_count, "Count")

    def failure(self) -> None:
        assert self._logger is not None
        self._logger.put_metric("DocsFailed", 1, "Count")

    def orphan(self) -> None:
        assert self._logger is not None
        self._logger.put_metric("OrphanUpload", 1, "Count")

    def service_down(self) -> None:
        assert self._logger is not None
        self._logger.put_metric("ServiceDownRetry", 1, "Count")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert self._logger is not None
        assert self._start is not None
        elapsed_ms = (time.monotonic() - self._start) * 1000
        self._logger.put_metric("IngestionDuration", elapsed_ms, "Milliseconds")
        await self._logger.flush()
        return False


def ingestion_metrics(*, strategy: str, correlation_id: str | None) -> IngestionMetrics:
    return IngestionMetrics(strategy=strategy, correlation_id=correlation_id)
