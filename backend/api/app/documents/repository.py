import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.documents.models import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        filename: str,
        s3_key: str,
        modality: str,
    ) -> Document:
        document = Document(
            tenant_id=tenant_id,
            filename=filename,
            s3_key=s3_key,
            modality=modality,
        )

        self.session.add(document)
        await self.session.flush()

        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )

        return result.scalar_one_or_none()

    async def list_for_tenant(self) -> list[Document]:
        result = await self.session.execute(select(Document))
        return list(result.scalars().all())

    async def update_status(self, document_id: uuid.UUID, status: str) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.status = status
        await self.session.flush()
        return document

    async def delete(self, document_id: uuid.UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document is None:
            return False

        await self.session.delete(document)
        await self.session.flush()
        return True