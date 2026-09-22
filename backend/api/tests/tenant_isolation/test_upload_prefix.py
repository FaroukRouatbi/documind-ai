def _make_spy(captured: dict):
    def _fake_generate_upload_post(
        s3_key: str, content_type: str, max_size_bytes: int = 50_000_000
    ):
        captured["s3_key"] = s3_key
        return {"url": "https://example.test/upload", "fields": {"key": s3_key}}

    return _fake_generate_upload_post


async def test_upload_key_uses_authenticated_tenant_not_client_input(
    client, as_tenant_a, seeded_tenants, monkeypatch
):
    captured: dict = {}
    monkeypatch.setattr("app.documents.router.generate_upload_post", _make_spy(captured))

    response = await client.post(
        "/v1/documents/upload",
        json={
            "filename": "report.md",
            "modality": "text",
            "content_type": "text/markdown",
            "tenant_id": str(seeded_tenants["tenant_b"]),
        },
    )

    assert response.status_code == 200
    assert captured["s3_key"].startswith(f"{as_tenant_a}/")
    assert str(seeded_tenants["tenant_b"]) not in captured["s3_key"]


async def test_upload_rejects_filename_that_tries_to_escape_prefix(
    client, as_tenant_a, monkeypatch
):
    captured: dict = {}
    monkeypatch.setattr("app.documents.router.generate_upload_post", _make_spy(captured))

    response = await client.post(
        "/v1/documents/upload",
        json={
            "filename": "../other-tenant/x.md",
            "modality": "text",
            "content_type": "text/markdown",
        },
    )

    assert response.status_code == 422
    assert captured == {}
