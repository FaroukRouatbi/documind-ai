import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    filename: Mapped[str] = mapped_column()
    s3_key: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(default="processing")
    modality: Mapped[str] = mapped_column()
    ingestion_strategy: Mapped[str | None] = mapped_column()