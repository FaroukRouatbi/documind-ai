# Imports every model so it registers on Base.metadata.
# Import once at app startup and in alembic/env.py — single source of truth.
from app.chunks.models import Chunk  # noqa: F401
from app.documents.models import Document  # noqa: F401
from app.tenants.models import Tenant  # noqa: F401
