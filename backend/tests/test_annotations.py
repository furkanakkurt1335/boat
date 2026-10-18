import pytest

from app.services.agreement import compute_annotation_agreement


@pytest.fixture
async def treebank_with_sentence(client, auth_headers):
    """Create a treebank and upload a sentence, return (treebank_id, sentence_id)."""
    tb_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Anno-TB", "language": "English"},
    )
    tb_id = tb_resp.json()["id"]

    conllu = (
        "# sent_id = anno-1\n"
        "# text = I run.\n"
        "1\tI\tI\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
        "2\trun\trun\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n"
        "\n"
    )
    await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", conllu.encode(), "text/plain")},
    )

    sents_resp = await client.get(f"/api/treebanks/{tb_id}/sentences", headers=auth_headers)
    sent_id = sents_resp.json()[0]["id"]
    return tb_id, sent_id


@pytest.mark.asyncio
async def test_create_annotation(client, auth_headers, treebank_with_sentence):
    _, sent_id = treebank_with_sentence
    response = await client.post(
        "/api/annotations",
        headers=auth_headers,
        json={"sentence_id": sent_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sentence_id"] == sent_id
    assert data["status"] == 0


@pytest.mark.asyncio
async def test_get_annotation_detail(client, auth_headers, treebank_with_sentence):
    _, sent_id = treebank_with_sentence
    create_resp = await client.post(
        "/api/annotations",
        headers=auth_headers,
        json={"sentence_id": sent_id},
    )
    anno_id = create_resp.json()["id"]

    response = await client.get(f"/api/annotations/{anno_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["annotator_username"] == "testuser"
    assert data["treebank_title"] == "Anno-TB"
    # Should have wordlines copied from template
    assert len(data["wordlines"]) == 3


@pytest.mark.asyncio
async def test_update_annotation_status(client, auth_headers, treebank_with_sentence):
    _, sent_id = treebank_with_sentence
    create_resp = await client.post(
        "/api/annotations",
        headers=auth_headers,
        json={"sentence_id": sent_id},
    )
    anno_id = create_resp.json()["id"]

    # Transition NEW -> DRAFT
    response = await client.patch(
        f"/api/annotations/{anno_id}",
        headers=auth_headers,
        json={"status": 1, "notes": "Done"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == 1
    assert response.json()["notes"] == "Done"


@pytest.mark.asyncio
async def test_batch_update_wordlines(client, auth_headers, treebank_with_sentence):
    _, sent_id = treebank_with_sentence
    create_resp = await client.post(
        "/api/annotations",
        headers=auth_headers,
        json={"sentence_id": sent_id},
    )
    anno_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/wordlines/annotations/{anno_id}",
        headers=auth_headers,
        json={
            "wordlines": [
                {"id_f": "1", "form": "I", "lemma": "I", "upos": "PRON"},
                {
                    "id_f": "2",
                    "form": "run",
                    "lemma": "run",
                    "upos": "VERB",
                    "head": "0",
                    "deprel": "root",
                },
                {"id_f": "3", "form": ".", "lemma": ".", "upos": "PUNCT"},
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["form"] == "I"
    assert data[1]["deprel"] == "root"


# Agreement unit tests (no HTTP needed)
_WL_CAT_NOUN = {
    "id_f": "1",
    "form": "cat",
    "lemma": "cat",
    "upos": "NOUN",
    "feats": "_",
    "head": "0",
    "deprel": "root",
}
_WL_CAT_VERB = {
    "id_f": "1",
    "form": "cat",
    "lemma": "cat",
    "upos": "VERB",
    "feats": "_",
    "head": "0",
    "deprel": "root",
}


def test_agreement_perfect():
    score = compute_annotation_agreement([[_WL_CAT_NOUN], [_WL_CAT_NOUN]])
    assert score == 1.0


def test_agreement_partial():
    score = compute_annotation_agreement([[_WL_CAT_NOUN], [_WL_CAT_VERB]])
    assert score == 0.75  # 3/4: feats, head, deprel match; upos doesn't


def test_agreement_multiword_returns_minus_one():
    wl = {
        "id_f": "1-2",
        "form": "don't",
        "lemma": "_",
        "upos": "_",
        "feats": "_",
        "head": "_",
        "deprel": "_",
    }
    score = compute_annotation_agreement([[wl]])
    assert score == -1
