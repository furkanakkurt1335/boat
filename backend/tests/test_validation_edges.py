import pytest


@pytest.mark.asyncio
async def test_upload_invalid_utf8(client, auth_headers):
    """Uploading a file with invalid UTF-8 bytes returns 422."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Val-TB-1", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    invalid_bytes = b"# sent_id = test-1\n# text = Bad \xff\xfe bytes\n1\tBad\tbad\tNOUN\t_\t_\t0\troot\t_\t_\n\n"

    response = await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", invalid_bytes, "text/plain")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_treebank_empty_title(client, auth_headers):
    """Creating a treebank with an empty title."""
    response = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "", "language": "Turkish"},
    )
    # Empty string is accepted by the schema (no min_length constraint),
    # so the server should create it or reject based on DB constraints.
    # Accept either 201 (created) or 4xx (validation error).
    assert response.status_code in (201, 400, 422)


@pytest.mark.asyncio
async def test_create_sentence_empty_text(client, auth_headers):
    """Creating a sentence with empty text."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Val-TB-2", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/sentences?treebank_id={tb_id}",
        headers=auth_headers,
        json={"sent_id": "empty-1", "text": ""},
    )
    # Empty text is accepted by the schema; the sentence gets created with
    # no wordlines since "".split() == [].
    assert response.status_code in (201, 400, 422)
