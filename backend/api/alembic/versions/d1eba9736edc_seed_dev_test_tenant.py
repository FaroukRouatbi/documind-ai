"""seed dev test tenant

Revision ID: d1eba9736edc
Revises: 540f348503de
Create Date: 2026-08-17 17:49:34.163067

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd1eba9736edc'
down_revision: str | Sequence[str] | None = '540f348503de'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO tenants (id, name)
        VALUES ('11111111-1111-1111-1111-111111111111', 'Test Tenant')
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM tenants WHERE id = '11111111-1111-1111-1111-111111111111'")
