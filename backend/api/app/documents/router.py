from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import API_V1_PREFIX
from app.core.database import get_tenant_db
from app.documents.repository import DocumentRepository

router = APIRouter(prefix=API_V1_PREFIX, tags=["documents"])

@router.get("/documents")
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    session : AsyncSession = Depends(get_tenant_db),
):
    repo = DocumentRepository(session)
    result = await repo.list_for_tenant(limit=limit, offset=offset)

    return {
        "documents": [
            {"id": doc.id, "filename": doc.filename, "status": doc.status}
            for doc in result.documents
        ],
        "total": result.total,
    }