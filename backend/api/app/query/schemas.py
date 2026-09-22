import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    heading_path: str | None
    content: str


class QueryResponse(BaseModel):
    query_id: str
    answer: str
    citations: list[Citation]
    truncated: bool
