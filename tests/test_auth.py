from unittest.mock import AsyncMock, patch


def test_missing_auth_header(client):
    r = client.post("/chat", json={"system": "test", "prompt": "hello"})
    assert r.status_code == 401


def test_invalid_api_key(client):
    r = client.post(
        "/chat",
        json={"system": "test", "prompt": "hello"},
        headers={"Authorization": "Bearer invalid-key"},
    )
    assert r.status_code == 401


def test_disabled_project(client, db, project):
    project.enabled = False
    db.flush()
    r = client.post(
        "/chat",
        json={"system": "test", "prompt": "hello"},
        headers={"Authorization": f"Bearer {project.api_key}"},
    )
    assert r.status_code == 401


def test_valid_api_key_accepted(client, auth_headers):
    with patch("app.routers.chat.llm.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            "response": "ok",
            "prompt_tokens": 5,
            "completion_tokens": 3,
            "duration_ms": 50,
        }
        r = client.post("/chat", json={"system": "s", "prompt": "p"}, headers=auth_headers)
    assert r.status_code == 200
