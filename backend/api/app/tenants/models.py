from app.core.database import Base
from app.core.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy.orm import Mapped, mapped_column

class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column()