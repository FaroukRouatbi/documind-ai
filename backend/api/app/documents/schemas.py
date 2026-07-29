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