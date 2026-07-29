from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import API_V1_PREFIX
from app.core.database import get_tenant_db
from app.documents.repository import DocumentRepository
from app.documents.schemas import DocumentResponse, PaginatedDocumentsResponse

router = APIRouter(prefix=API_V1_PREFIX, tags=["documents"])

@router.get("/documents", response_model=PaginatedDocumentsResponse)
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    session : AsyncSession = Depends(get_tenant_db),
):
    repo = DocumentRepository(session)
    result = await repo.list_for_tenant(limit=limit, offset=offset)

    return {
        "documents": [DocumentResponse.model_validate(doc) for doc in result.documents],
        "total": result.total,
    }