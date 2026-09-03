async def test_list_documents_returns_paginated_shape(
    client, override_current_user, override_tenant_db
):
    response = await client.get("/v1/documents")

    assert response.status_code == 200
    body = response.json()
    assert "documents" in body
    assert "total" in body
    assert isinstance(body["documents"], list)
