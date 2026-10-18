import pytest


@pytest.mark.asyncio
async def test_create_treebank(client, auth_headers):
    response = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Test-TB", "language": "Turkish"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test-TB"
    assert data["language"] == "Turkish"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_treebank(client, auth_headers):
    await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Dup-TB", "language": "English"},
    )
    response = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Dup-TB", "language": "English"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_treebanks(client, auth_headers):
    await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "List-TB", "language": "Arabic"},
    )
    response = await client.get("/api/treebanks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "sentence_count" in data[0]


@pytest.mark.asyncio
async def test_get_treebank(client, auth_headers):
    create_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Get-TB", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]
    response = await client.get(f"/api/treebanks/{tb_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get-TB"


@pytest.mark.asyncio
async def test_delete_treebank(client, auth_headers):
    create_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Del-TB", "language": "English"},
    )
    tb_id = create_resp.json()["id"]
    response = await client.delete(f"/api/treebanks/{tb_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/api/treebanks/{tb_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_conllu(client, auth_headers):
    create_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Upload-TB", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    conllu_content = (
        "# sent_id = test-1\n"
        "# text = Bu bir test.\n"
        "1\tBu\tbu\tDET\t_\t_\t3\tdet\t_\t_\n"
        "2\tbir\tbir\tDET\t_\t_\t3\tdet\t_\t_\n"
        "3\ttest\ttest\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_\n"
        "\n"
    )

    response = await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", conllu_content.encode(), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["sentences_created"] == 1

    # Verify sentences were created
    response = await client.get(f"/api/treebanks/{tb_id}/sentences", headers=auth_headers)
    assert response.status_code == 200
    sentences = response.json()
    assert len(sentences) == 1
    assert sentences[0]["sent_id"] == "test-1"


@pytest.mark.asyncio
async def test_languages(client, auth_headers):
    response = await client.get("/api/treebanks/languages", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "Turkish" in data
    assert data["Turkish"] == "tr"
