from abc import ABC, abstractmethod

from app.documents.models import Document
from app.ingestion.schemas import ChunkData


class IngestionStrategy(ABC):
    @abstractmethod
    async def process(self, document: Document, file_bytes: bytes) -> list[ChunkData]:
        ...
