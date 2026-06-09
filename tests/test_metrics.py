from app.config import settings


def _admin_headers():
    return {"Authorization": f"Bearer {settings.metrics_api_key}"}


def test_metrics_no_auth_header(client):
    r = client.get("/metrics")
    assert r.status_code == 401


def test_metrics_wrong_key(client):
    r = client.get("/metrics", headers={"Authorization": "Bearer definitely-wrong"})
    assert r.status_code == 403


def test_metrics_success(client):
    r = client.get("/metrics", headers=_admin_headers())
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) >= {
        "requests_today",
        "requests_by_project",
        "avg_duration_ms",
        "total_tokens",
        "errors_today",
    }


def test_metrics_empty_counts(client):
    r = client.get("/metrics", headers=_admin_headers())
    body = r.json()
    assert body["requests_today"] == 0
    assert body["requests_by_project"] == {}
    assert body["total_tokens"] == 0
