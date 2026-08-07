import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Chunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chunks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    parent_chunk_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chunks.id"), index=True)
    chunk_index: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column()
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    embedding_model: Mapped[str] = mapped_column()
    embedding_version: Mapped[int] = mapped_column()
    heading_path: Mapped[str | None] = mapped_column(nullable=True)
    ingestion_strategy: Mapped[str] = mapped_column()
    token_count: Mapped[int | None] = mapped_column(nullable=True)