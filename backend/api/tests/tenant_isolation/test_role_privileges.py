from sqlalchemy import text

from app.core.config import settings


async def test_app_role_has_least_privilege_attributes(owner_sessionmaker):
    async with owner_sessionmaker() as session:
        result = await session.execute(
            text(
                "SELECT rolcanlogin, rolbypassrls, rolsuper "
                "FROM pg_roles WHERE rolname = :role"
            ),
            {"role": settings.db.username},
        )
        row = result.mappings().first()

    assert row is not None, f"role {settings.db.username!r} not found in pg_roles"
    assert row["rolcanlogin"] is True
    assert row["rolbypassrls"] is False
    assert row["rolsuper"] is False

async def test_app_role_not_own_rls_tables(owner_sessionmaker):
    async with owner_sessionmaker() as session:
        result = await session.execute(
            text(
                "SELECT tablename, tableowner FROM pg_tables "
                "WHERE tablename IN ('documents', 'chunks')"
            )
        )
        rows = result.mappings().all()

    owners = {row["tablename"]: row["tableowner"] for row in rows}

    assert "documents" in owners
    assert "chunks" in owners
    assert owners["documents"] != settings.db.username
    assert owners["chunks"] != settings.db.username
