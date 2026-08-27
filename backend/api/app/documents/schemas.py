import uuid

from pydantic import BaseModel, Field, field_validator


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str

    model_config = {"from_attributes": True}


class PaginatedDocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class UploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    modality: str
    content_type: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("filename must not be blank")
        if "/" in v or "\\" in v:
            raise ValueError("filename must not contain path separators")
        if any(ord(c) < 32 for c in v):
            raise ValueError("filename must not contain control characters")
        return v


class UploadResponse(BaseModel):
    document_id: uuid.UUID
    upload_url: str
    upload_fields: dict
