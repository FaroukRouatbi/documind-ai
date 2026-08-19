import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import get_contextvars

from app.core.config import API_V1_PREFIX
from app.core.database import get_tenant_db
from app.documents.repository import DocumentRepository
from app.documents.schemas import DocumentResponse, PaginatedDocumentsResponse, UploadRequest, UploadResponse
from app.core.security import get_current_user
from app.documents.s3 import generate_upload_post

router = APIRouter(prefix=API_V1_PREFIX, tags=["documents"])

@router.get("/documents",
            response_model=PaginatedDocumentsResponse,
            summary="List documents for the current tenant",
)
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    session : AsyncSession = Depends(get_tenant_db),
):
    """
    Returns a paginated list of documents belonging to the authenticated
    user's tenant. Results are automatically scoped by row-level security.
    """
    repo = DocumentRepository(session)
    result = await repo.list_for_tenant(limit=limit, offset=offset)

    return {
        "documents": [DocumentResponse.model_validate(doc) for doc in result.documents],
        "total": result.total,
    }

@router.post("/documents/upload", response_model=UploadResponse, summary="Get a presigned upload URL")
async def create_upload(
        request: UploadRequest,
        current_user: dict = Depends(get_current_user),
        session: AsyncSession = Depends(get_tenant_db),
):
    
    """
    Creates a document record and returns a presigned S3 POST for the client
    to upload the file directly, bypassing the API server.
    """
    tenant_id = current_user["tenant_id"]
    s3_key = f"{tenant_id}/{uuid.uuid4()}-{request.filename}"

    repo = DocumentRepository(session)

    correlation_id = get_contextvars().get("correlation_id")

    document = await repo.create(
        tenant_id=tenant_id,
        filename=request.filename,
        s3_key=s3_key,
        modality=request.modality,
        correlation_id=correlation_id,
    )

    presigned = generate_upload_post(s3_key, request.content_type)

    return UploadResponse(
        document_id=document.id,
        upload_url=presigned["url"],
        upload_fields=presigned["fields"],
    )