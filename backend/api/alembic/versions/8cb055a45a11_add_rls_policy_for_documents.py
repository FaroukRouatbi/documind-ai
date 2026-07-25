"""add rls policy for documents

Revision ID: 8cb055a45a11
Revises: 372749ccd975
Create Date: 2026-07-25 16:18:56.975295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cb055a45a11'
down_revision: Union[str, Sequence[str], None] = '372749ccd975'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON documents
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP POLICY tenant_isolation ON documents")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY")