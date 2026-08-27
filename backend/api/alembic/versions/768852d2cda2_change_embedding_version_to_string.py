"""change embedding_version to string

Revision ID: 768852d2cda2
Revises: d1eba9736edc
Create Date: 2026-08-18 13:03:14.675591

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '768852d2cda2'
down_revision: str | Sequence[str] | None = 'd1eba9736edc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("chunks", "embedding_version",
                    existing_type=sa.Integer(),
                    type_=sa.String(),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column("chunks", "embedding_version",
                    existing_type=sa.String(),
                    type_=sa.Integer(),
                    existing_nullable=False)
