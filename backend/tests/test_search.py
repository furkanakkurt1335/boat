import pytest


@pytest.fixture
async def populated_treebank(client, auth_headers):
    """Create a treebank with uploaded sentences for search testing."""
    tb_resp = await client.post(
        "/api/treebanks",
        headers=auth_headers,
        json={"title": "Search-TB", "language": "English"},
    )
    tb_id = tb_resp.json()["id"]

    conllu = (
        "# sent_id = s1\n"
        "# text = The cat sat.\n"
        "1\tThe\tthe\tDET\t_\t_\t2\tdet\t_\t_\n"
        "2\tcat\tcat\tNOUN\t_\tNumber=Sing\t3\tnsubj\t_\t_\n"
        "3\tsat\tsit\tVERB\t_\tTense=Past\t0\troot\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_\n"
        "\n"
        "# sent_id = s2\n"
        "# text = Dogs bark loudly.\n"
        "1\tDogs\tdog\tNOUN\t_\tNumber=Plur\t2\tnsubj\t_\t_\n"
        "2\tbark\tbark\tVERB\t_\tTense=Pres\t0\troot\t_\t_\n"
        "3\tloudly\tloudly\tADV\t_\t_\t2\tadvmod\t_\tSpaceAfter=No\n"
        "4\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n"
        "\n"
    )
    await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=auth_headers,
        files={"file": ("test.conllu", conllu.encode(), "text/plain")},
    )
    return tb_id


@pytest.mark.asyncio
async def test_search_by_upos(client, auth_headers, populated_treebank):
    response = await client.get("/api/search", headers=auth_headers, params={"upos": "NOUN"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["results"]) >= 2
    assert all(r["upos"] == "NOUN" for r in data["results"])


@pytest.mark.asyncio
async def test_search_by_form(client, auth_headers, populated_treebank):
    response = await client.get("/api/search", headers=auth_headers, params={"form": "cat"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 1
    assert data["results"][0]["form"] == "cat"
    assert data["results"][0]["treebank_title"] == "Search-TB"


@pytest.mark.asyncio
async def test_search_by_deprel(client, auth_headers, populated_treebank):
    response = await client.get("/api/search", headers=auth_headers, params={"deprel": "root"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 2


@pytest.mark.asyncio
async def test_search_by_treebank_title(client, auth_headers, populated_treebank):
    response = await client.get(
        "/api/search", headers=auth_headers, params={"treebank_title": "Search"}
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1


@pytest.mark.asyncio
async def test_search_empty_results(client, auth_headers, populated_treebank):
    response = await client.get(
        "/api/search", headers=auth_headers, params={"form": "nonexistent"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_search_with_pagination(client, auth_headers, populated_treebank):
    response = await client.get(
        "/api/search",
        headers=auth_headers,
        params={"limit": 2, "offset": 0},
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 2
