import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document


@dataclass
class PaginatedDocuments:
    documents: list[Document]
    total: int


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        filename: str,
        s3_key: str,
        modality: str,
        correlation_id: str | None = None,
    ) -> Document:
        document = Document(
            tenant_id=tenant_id,
            filename=filename,
            s3_key=s3_key,
            modality=modality,
            status="pending",
            correlation_id=correlation_id,
        )

        self.session.add(document)
        await self.session.flush()

        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.id == document_id))

        return result.scalar_one_or_none()

    async def list_for_tenant(self, limit: int = 20, offset: int = 0) -> PaginatedDocuments:
        result = await self.session.execute(select(Document).limit(limit).offset(offset))
        documents = list(result.scalars().all())

        count_result = await self.session.execute(select(func.count()).select_from(Document))
        total = count_result.scalar_one()

        return PaginatedDocuments(documents=documents, total=total)

    async def update_status(self, document_id: uuid.UUID, status: str) -> bool:
        stmt = update(Document).where(Document.id == document_id).values(status=status)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def delete(self, document_id: uuid.UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document is None:
            return False

        await self.session.delete(document)
        await self.session.flush()
        return True

    async def get_by_s3_key(self, s3_key: str) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.s3_key == s3_key))
        return result.scalar_one_or_none()
