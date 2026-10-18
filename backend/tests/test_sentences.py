import pytest


@pytest.fixture
async def treebank_id(client, auth_headers):
    resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Sent-TB", "language": "Turkish"},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_sentence(client, auth_headers, treebank_id):
    response = await client.post(
        "/api/sentences",
        headers=auth_headers,
        params={"treebank_id": treebank_id},
        json={"sent_id": "s1", "text": "Bu bir test cümlesidir"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sent_id"] == "s1"
    assert data["text"] == "Bu bir test cümlesidir"
    assert data["order"] == 1


@pytest.mark.asyncio
async def test_get_sentence(client, auth_headers, treebank_id):
    create_resp = await client.post(
        "/api/sentences",
        headers=auth_headers,
        params={"treebank_id": treebank_id},
        json={"sent_id": "s1", "text": "Test sentence"},
    )
    sent_id = create_resp.json()["id"]

    response = await client.get(f"/api/sentences/{sent_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["text"] == "Test sentence"


@pytest.mark.asyncio
async def test_get_sentence_not_found(client, auth_headers):
    response = await client.get("/api/sentences/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_sentence(client, auth_headers, treebank_id):
    create_resp = await client.post(
        "/api/sentences",
        headers=auth_headers,
        params={"treebank_id": treebank_id},
        json={"sent_id": "del-s1", "text": "To be deleted"},
    )
    sent_id = create_resp.json()["id"]

    response = await client.delete(f"/api/sentences/{sent_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/api/sentences/{sent_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_sentence_annotations(client, auth_headers, treebank_id):
    # Upload a file to get a sentence with a template annotation
    conllu = (
        "# sent_id = annos-s1\n"
        "# text = Hello world\n"
        "1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_\n"
        "2\tworld\tworld\tNOUN\t_\t_\t1\tvocative\t_\t_\n"
        "\n"
    )
    await client.post(
        f"/api/treebanks/{treebank_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", conllu.encode(), "text/plain")},
    )

    # Get the sentence
    sents_resp = await client.get(f"/api/treebanks/{treebank_id}/sentences", headers=auth_headers)
    sent_id = sents_resp.json()[0]["id"]

    response = await client.get(f"/api/sentences/{sent_id}/annotations", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1  # at least template annotation


@pytest.mark.asyncio
async def test_auto_increment_order(client, auth_headers, treebank_id):
    resp1 = await client.post(
        "/api/sentences",
        headers=auth_headers,
        params={"treebank_id": treebank_id},
        json={"sent_id": "inc-1", "text": "First"},
    )
    resp2 = await client.post(
        "/api/sentences",
        headers=auth_headers,
        params={"treebank_id": treebank_id},
        json={"sent_id": "inc-2", "text": "Second"},
    )
    assert resp1.json()["order"] == 1
    assert resp2.json()["order"] == 2
