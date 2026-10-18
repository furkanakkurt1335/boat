import pytest


@pytest.fixture(autouse=True)
def _open_registration(monkeypatch):
    """These fixtures register users via the API; put the app in open mode
    so the accounts are active and login succeeds (default mode is approval,
    which leaves new users inactive -> login 403)."""
    monkeypatch.setattr("app.core.config.settings.REGISTRATION_MODE", "open")


async def register_and_login(client, username, email, password):
    """Register a user and return auth headers."""
    await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "first_name": "Test",
            "last_name": "User",
            "password": password,
        },
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_a_headers(client):
    return await register_and_login(client, "user_a", "a@example.com", "password_a")


@pytest.fixture
async def user_b_headers(client):
    return await register_and_login(client, "user_b", "b@example.com", "password_b")


@pytest.mark.asyncio
async def test_delete_treebank_unauthorized(client, user_a_headers, user_b_headers):
    """User B cannot delete a treebank created by user A."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=user_a_headers,
        json={"title": "AuthZ-TB-1", "language": "Turkish"},
    )
    assert create_resp.status_code == 201
    tb_id = create_resp.json()["id"]

    response = await client.delete(f"/api/treebanks/{tb_id}", headers=user_b_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_treebank_authorized(client, user_a_headers):
    """Owner can delete their own treebank."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=user_a_headers,
        json={"title": "AuthZ-TB-2", "language": "Turkish"},
    )
    assert create_resp.status_code == 201
    tb_id = create_resp.json()["id"]

    response = await client.delete(f"/api/treebanks/{tb_id}", headers=user_a_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_sentence_unauthorized(client, user_a_headers, user_b_headers):
    """User B cannot delete a sentence in a treebank created by user A."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=user_a_headers,
        json={"title": "AuthZ-TB-3", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    sent_resp = await client.post(
        f"/api/sentences?treebank_id={tb_id}",
        headers=user_a_headers,
        json={"sent_id": "s1", "text": "Bu bir test."},
    )
    assert sent_resp.status_code == 201
    sent_id = sent_resp.json()["id"]

    response = await client.delete(f"/api/sentences/{sent_id}", headers=user_b_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_sentence_authorized(client, user_a_headers):
    """Treebank creator can delete sentences in their treebank."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=user_a_headers,
        json={"title": "AuthZ-TB-4", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    sent_resp = await client.post(
        f"/api/sentences?treebank_id={tb_id}",
        headers=user_a_headers,
        json={"sent_id": "s1", "text": "Bu bir test."},
    )
    assert sent_resp.status_code == 201
    sent_id = sent_resp.json()["id"]

    response = await client.delete(f"/api/sentences/{sent_id}", headers=user_a_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_upload_conllu_unauthorized(client, user_a_headers, user_b_headers):
    """User B cannot upload CoNLL-U to a treebank created by user A."""
    create_resp = await client.post(
        "/api/treebanks",
        headers=user_a_headers,
        json={"title": "AuthZ-TB-5", "language": "Turkish"},
    )
    tb_id = create_resp.json()["id"]

    conllu_content = (
        "# sent_id = test-1\n"
        "# text = Test.\n"
        "1\tTest\ttest\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n"
        "\n"
    )

    response = await client.post(
        f"/api/treebanks/{tb_id}/upload",
        headers=user_b_headers,
        files={"file": ("test.conllu", conllu_content.encode(), "text/plain")},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_access(client):
    """Protected endpoints return 401 without a token."""
    endpoints = [
        ("GET", "/api/treebanks"),
        ("POST", "/api/treebanks"),
        ("GET", "/api/treebanks/1"),
        ("DELETE", "/api/treebanks/1"),
        ("GET", "/api/sentences/1"),
        ("GET", "/api/auth/me"),
    ]
    for method, url in endpoints:
        response = await getattr(client, method.lower())(url)
        assert response.status_code == 401, f"{method} {url} returned {response.status_code}"
