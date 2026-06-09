from unittest.mock import AsyncMock, patch


def test_health_llm_running(client):
    with patch("app.routers.health.llm.health_check", new_callable=AsyncMock, return_value=True):
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llama_cpp"] == "running"


def test_health_llm_unavailable(client):
    with patch("app.routers.health.llm.health_check", new_callable=AsyncMock, return_value=False):
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llama_cpp"] == "unavailable"


def test_health_model_name_in_response(client):
    with patch("app.routers.health.llm.health_check", new_callable=AsyncMock, return_value=True):
        r = client.get("/health")
    assert "model" in r.json()
