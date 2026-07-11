"""
tests/integration/test_security.py

Edge-case integration tests covering security hardening:
  - Security headers on every response
  - Session cookie flags
  - 404 / 500 error handler JSON shape
"""

from __future__ import annotations

import json


class TestSecurityHeaders:
    """Every response from the banking Blueprint must carry defensive headers."""

    def _get_headers(self, client, path: str = "/login"):
        res = client.get(path)
        return res.headers

    def test_x_frame_options_present(self, client):
        headers = self._get_headers(client)
        assert headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_x_content_type_options_present(self, client):
        headers = self._get_headers(client)
        assert headers.get("X-Content-Type-Options") == "nosniff"

    def test_referrer_policy_present(self, client):
        headers = self._get_headers(client)
        assert "Referrer-Policy" in headers

    def test_content_security_policy_present(self, client):
        headers = self._get_headers(client)
        assert "Content-Security-Policy" in headers

    def test_csp_allows_bootstrap_cdn(self, client):
        csp = self._get_headers(client).get("Content-Security-Policy", "")
        assert "cdn.jsdelivr.net" in csp

    def test_security_headers_on_api_endpoint(self, auth_client):
        res = auth_client.get("/balance")
        assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_security_headers_on_error_response(self, client):
        res = client.get("/this-route-does-not-exist")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"


class TestErrorHandlers:
    """Flask error handlers must return consistent JSON."""

    def test_404_returns_json(self, client):
        res = client.get("/this-does-not-exist")
        assert res.status_code == 404
        data = json.loads(res.data)
        assert "error" in data

    def test_404_error_message_not_empty(self, client):
        res = client.get("/missing-page")
        data = json.loads(res.data)
        assert data["error"]

    def test_401_unauthenticated_api_returns_json(self, client):
        res = client.get("/balance")
        assert res.status_code == 401
        data = json.loads(res.data)
        assert "error" in data


class TestSessionCookieFlags:
    """A session cookie must be set after successful login."""

    def test_session_cookie_exists_after_login(self, client):
        import json as _json
        res = client.post(
            "/login",
            data=_json.dumps({"username": "alice", "password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 200
        # Flask 3.x: use get_cookie() to inspect cookies
        cookie = client.get_cookie("session")
        assert cookie is not None, "No session cookie found after login"
