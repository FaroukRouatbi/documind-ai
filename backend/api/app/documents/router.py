from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.documents.repository import DocumentRepository
from app.core.security import get_current_user


router = APIRouter(prefix="/v1", tags=["documents"])

@router.post("/documents/test-create")
async def test_create_document(
    session: AsyncSession = Depends(get_tenant_db),
    current_user: dict = Depends(get_current_user),
):
    repo = DocumentRepository(session)
    document = await repo.create(
        tenant_id=current_user["tenant_id"],
        filename="test.pdf",
        s3_key="test-key",
        modality="text",
    )
    return {"id": str(document.id), "tenant_id": str(document.tenant_id)}