"""add rls policy for chunks

Revision ID: 9352792701d3
Revises: de24c55430b0
Create Date: 2026-08-05 02:53:19.618757

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9352792701d3'
down_revision: str | Sequence[str] | None = 'de24c55430b0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON chunks
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY tenant_isolation ON chunks")
    op.execute("ALTER TABLE chunks DISABLE ROW LEVEL SECURITY")
