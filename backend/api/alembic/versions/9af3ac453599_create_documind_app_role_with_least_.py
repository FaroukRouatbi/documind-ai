"""create documind_app role with least-privilege grants

Revision ID: 9af3ac453599
Revises: 6358bb32b8c2
Create Date: 2026-08-22 14:43:22.210631

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '9af3ac453599'
down_revision: Union[str, Sequence[str], None] = '6358bb32b8c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    password = os.environ.get("DOCUMIND_APP_PASSWORD")
    if not password:
        raise RuntimeError("DOCUMIND_APP_PASSWORD not set — cannot create app role")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'documind_app') THEN
                CREATE ROLE documind_app WITH LOGIN;
            END IF;
        END
        $$;
    """)

    conn = op.get_bind()
    alter_sql = conn.execute(
        text("SELECT format('ALTER ROLE documind_app WITH PASSWORD %L', CAST(:pw AS text))"),
        {"pw": password},
    ).scalar()
    conn.execute(text(alter_sql))

    op.execute("GRANT CONNECT ON DATABASE documind TO documind_app;")
    op.execute("GRANT USAGE ON SCHEMA public TO documind_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON documents, tenants, chunks TO documind_app;")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'documind_app' AND rolbypassrls) THEN
                RAISE EXCEPTION 'documind_app must NOT have BYPASSRLS';
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON documents, tenants, chunks FROM documind_app;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM documind_app;")
    op.execute("REVOKE CONNECT ON DATABASE documind FROM documind_app;")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'documind_app') THEN
                DROP ROLE documind_app;
            END IF;
        END
        $$;
    """)
