"""Tests for static frontend assets and HTML routing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import DEFAULT_FRONTEND_DIR, Settings
from app.main import create_app


def test_index_html_served_at_root(tmp_path) -> None:
    settings = Settings(db_path=tmp_path / "test.db", frontend_dir=DEFAULT_FRONTEND_DIR, serve_frontend=True)
    with TestClient(create_app(settings)) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert 'dir="rtl"' in resp.text
        assert 'lang="he"' in resp.text
        assert "רשימת אריזה משפחתית" in resp.text


def test_static_assets_served_with_no_cache_header(tmp_path) -> None:
    settings = Settings(db_path=tmp_path / "test.db", frontend_dir=DEFAULT_FRONTEND_DIR, serve_frontend=True)
    with TestClient(create_app(settings)) as client:
        # CSS
        css_resp = client.get("/css/tokens.css")
        assert css_resp.status_code == 200
        assert "no-cache" in css_resp.headers["cache-control"]

        # JS
        js_resp = client.get("/js/app.js")
        assert js_resp.status_code == 200
        assert "no-cache" in js_resp.headers["cache-control"]

        # Manifest
        manifest_resp = client.get("/manifest.webmanifest")
        assert manifest_resp.status_code == 200

        # Icon SVG
        icon_resp = client.get("/icon.svg")
        assert icon_resp.status_code == 200
        assert "image/svg+xml" in icon_resp.headers["content-type"]
