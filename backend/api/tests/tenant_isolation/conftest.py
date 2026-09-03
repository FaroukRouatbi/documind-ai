import pytest_asyncio
from sqlalchemy import text

from app.documents.models import Document
from app.tenants.models import Tenant


@pytest_asyncio.fixture
async def seeded_tenants(owner_sessionmaker):
    async with owner_sessionmaker() as session:
        async with session.begin():
            tenant_a = Tenant(name="Tenant A")
            tenant_b = Tenant(name="Tenant B")
            session.add_all([tenant_a, tenant_b])
            await session.flush()

            doc_a = Document(
                tenant_id=tenant_a.id,
                filename="a.md",
                s3_key=f"{tenant_a.id}/a.md",
                modality="text",
            )
            doc_b = Document(
                tenant_id=tenant_b.id,
                filename="b.md",
                s3_key=f"{tenant_b.id}/b.md",
                modality="text",
            )
            session.add_all([doc_a, doc_b])
            await session.flush()

            data = {
                "tenant_a": tenant_a.id,
                "tenant_b": tenant_b.id,
                "doc_a": doc_a.id,
                "doc_b": doc_b.id,
                "doc_a_s3_key": doc_a.s3_key,
                "doc_b_s3_key": doc_b.s3_key,
            }

    yield data

    async with owner_sessionmaker() as session:
        async with session.begin():
            await session.execute(
                text("DELETE FROM documents WHERE tenant_id = ANY(:ids)"),
                {"ids": [data["tenant_a"], data["tenant_b"]]},
            )
            await session.execute(
                text("DELETE FROM tenants WHERE id = ANY(:ids)"),
                {"ids": [data["tenant_a"], data["tenant_b"]]},
            )
