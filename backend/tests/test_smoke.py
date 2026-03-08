"""
Backend API smoke tests.
Uses FastAPI TestClient -- no running server required.
Env vars are set in conftest.py before any import happens.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Schema / tables
# ---------------------------------------------------------------------------

def test_schema_endpoint_reachable(client):
    resp = client.get("/api/v1/schema")
    assert resp.status_code == 200
    body = resp.json()
    assert "tables" in body


def test_tables_endpoint_returns_list(client):
    resp = client.get("/api/v1/tables")
    assert resp.status_code == 200
    body = resp.json()
    assert "tables" in body
    assert isinstance(body["tables"], list)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def test_chat_rejects_empty_question(client):
    resp = client.post("/api/v1/chat", json={"question": ""})
    assert resp.status_code == 400


def test_chat_rejects_whitespace_question(client):
    resp = client.post("/api/v1/chat", json={"question": "   "})
    assert resp.status_code == 400


def test_chat_missing_body_returns_error(client):
    resp = client.post("/api/v1/chat")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_sessions_list_returns_list(client):
    resp = client.get("/api/v1/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert "sessions" in body
    assert isinstance(body["sessions"], list)


def test_session_not_found(client):
    resp = client.get("/api/v1/sessions/nonexistent-session-id-xyz")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def test_metrics_summary_reachable(client):
    resp = client.get("/api/v1/metrics/summary")
    assert resp.status_code == 200


def test_metrics_queries_reachable(client):
    resp = client.get("/api/v1/metrics/queries")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Voice token
# ---------------------------------------------------------------------------

def test_voice_token_returns_503_when_not_configured(client):
    """LiveKit keys are intentionally empty in test env (set in conftest.py)."""
    resp = client.post("/api/v1/voice/token", json={})
    assert resp.status_code == 503


def test_voice_token_payload_schema(client):
    """Token endpoint validates the request body structure."""
    resp = client.post("/api/v1/voice/token", json={"session_id": "test-session"})
    # 503 because LiveKit is not configured in test env
    assert resp.status_code == 503
    assert "detail" in resp.json()
