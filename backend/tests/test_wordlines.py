import pytest


@pytest.fixture
async def annotation_id(client, auth_headers):
    """Create a treebank, upload a sentence, create an annotation, return its ID."""
    tb_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "WL-TB", "language": "English"},
    )
    tb_id = tb_resp.json()["id"]

    conllu = (
        "# sent_id = wl-1\n"
        "# text = Hello world\n"
        "1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_\n"
        "2\tworld\tworld\tNOUN\t_\t_\t1\tvocative\t_\t_\n"
        "\n"
    )
    await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", conllu.encode(), "text/plain")},
    )

    sents = await client.get(f"/api/treebanks/{tb_id}/sentences", headers=auth_headers)
    sent_id = sents.json()[0]["id"]

    anno_resp = await client.post(
        "/api/annotations",
        headers=auth_headers,
        json={"sentence_id": sent_id},
    )
    return anno_resp.json()["id"]


@pytest.mark.asyncio
async def test_list_wordlines(client, auth_headers, annotation_id):
    response = await client.get(
        f"/api/wordlines/annotations/{annotation_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["form"] == "Hello"


@pytest.mark.asyncio
async def test_batch_update_replaces_all(client, auth_headers, annotation_id):
    # First, verify we have 2 wordlines
    resp = await client.get(
        f"/api/wordlines/annotations/{annotation_id}",
        headers=auth_headers,
    )
    assert len(resp.json()) == 2

    # Replace with 3 wordlines
    response = await client.put(
        f"/api/wordlines/annotations/{annotation_id}",
        headers=auth_headers,
        json={
            "wordlines": [
                {"id_f": "1", "form": "Hi", "lemma": "hi", "upos": "INTJ"},
                {"id_f": "2", "form": "beautiful", "lemma": "beautiful", "upos": "ADJ"},
                {"id_f": "3", "form": "world", "lemma": "world", "upos": "NOUN"},
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["form"] == "Hi"
    assert data[1]["upos"] == "ADJ"


@pytest.mark.asyncio
async def test_batch_update_not_found(client, auth_headers):
    response = await client.put(
        "/api/wordlines/annotations/99999",
        headers=auth_headers,
        json={"wordlines": [{"id_f": "1", "form": "x", "lemma": "x"}]},
    )
    assert response.status_code == 404
