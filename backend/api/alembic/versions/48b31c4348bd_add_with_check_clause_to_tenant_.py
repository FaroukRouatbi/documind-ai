"""add with check clause to tenant isolation policy

Revision ID: 48b31c4348bd
Revises: 8cb055a45a11
Create Date: 2026-07-25 20:56:29.542694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48b31c4348bd'
down_revision: Union[str, Sequence[str], None] = '8cb055a45a11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP POLICY tenant_isolation ON documents")
    op.execute("""
        CREATE POLICY tenant_isolation ON documents
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)
""")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DrOP POLICY tenant_isolation ON documents")
    op.execute("""
        CREATE POLICY tenant_isolation ON documents
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
""")
