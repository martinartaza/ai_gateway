import httpx
import pytest
from unittest.mock import AsyncMock, patch

from app.models import Request as RequestLog

LLM_RESULT = {
    "response": "Hello there!",
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "duration_ms": 123,
}


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("app.routers.chat.llm.generate", new_callable=AsyncMock) as m:
        m.return_value = LLM_RESULT
        yield m


def test_chat_success(client, auth_headers):
    r = client.post(
        "/chat",
        json={"system": "You are helpful", "prompt": "Hi"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["response"] == "Hello there!"
    assert body["tokens"] == 15
    assert body["duration_ms"] == 123


def test_chat_logs_request(client, db, auth_headers, project):
    client.post("/chat", json={"system": "sys", "prompt": "test prompt"}, headers=auth_headers)
    log = db.query(RequestLog).filter_by(project_id=project.id).first()
    assert log is not None
    assert log.prompt == "test prompt"
    assert log.duration_ms == 123
    assert log.prompt_tokens == 10
    assert log.completion_tokens == 5


def test_chat_empty_prompt(client, auth_headers):
    r = client.post("/chat", json={"system": "sys", "prompt": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_empty_system(client, auth_headers):
    r = client.post("/chat", json={"system": "", "prompt": "hello"}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_whitespace_prompt(client, auth_headers):
    r = client.post("/chat", json={"system": "sys", "prompt": "   "}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_llm_unavailable_returns_502(client, auth_headers):
    with patch("app.routers.chat.llm.generate", new_callable=AsyncMock) as m:
        m.side_effect = httpx.ConnectError("refused")
        r = client.post("/chat", json={"system": "s", "prompt": "p"}, headers=auth_headers)
    assert r.status_code == 502


def test_chat_llm_error_logs_null_response(client, db, auth_headers, project):
    with patch("app.routers.chat.llm.generate", new_callable=AsyncMock) as m:
        m.side_effect = httpx.ConnectError("refused")
        client.post("/chat", json={"system": "s", "prompt": "err"}, headers=auth_headers)
    log = db.query(RequestLog).filter_by(project_id=project.id).first()
    assert log is not None
    assert log.response is None
