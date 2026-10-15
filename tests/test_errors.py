"""Error envelope, health and HTTP-level behaviour."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["schema_version"] == 1


def test_not_found_envelope(client: TestClient) -> None:
    resp = client.get("/api/trips/999")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "not_found", "message": "Trip 999 not found"}}


def test_unknown_route_envelope(client: TestClient) -> None:
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_validation_envelope(client: TestClient) -> None:
    resp = client.post("/api/trips", json={"name": ""})
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert err["code"] == "validation_error"
    assert err["details"][0]["loc"] == ["body", "name"]


def test_malformed_json(client: TestClient) -> None:
    resp = client.post("/api/trips", content=b"{not json", headers={"content-type": "application/json"})
    assert resp.status_code == 422


def test_method_not_allowed(client: TestClient) -> None:
    resp = client.put("/api/trips")
    assert resp.status_code == 405
    assert resp.json()["error"]["code"] == "method_not_allowed"


def test_path_param_validation(client: TestClient) -> None:
    assert client.get("/api/trips/abc").status_code == 422


def test_api_responses_not_cached(client: TestClient) -> None:
    resp = client.get("/api/trips")
    assert resp.headers["cache-control"] == "no-store"
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_unhandled_exception_returns_500_envelope(tmp_path) -> None:
    from app.config import Settings
    from app.main import create_app

    settings = Settings(db_path=tmp_path / "test.db", serve_frontend=False)
    app = create_app(settings)

    @app.get("/api/boom")
    async def boom() -> None:
        raise RuntimeError("kaboom")

    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.get("/api/boom")
    assert resp.status_code == 500
    assert resp.json() == {"error": {"code": "internal_error", "message": "Internal server error"}}
