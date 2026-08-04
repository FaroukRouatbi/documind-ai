import uuid
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str

    model_config = {"from_attributes": True}

class PaginatedDocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int

class UploadRequest(BaseModel):
    filename: str
    modality: str
    content_type: str

class UploadResponse(BaseModel):
    document_id: uuid.UUID
    upload_url: str
    upload_fields: dict