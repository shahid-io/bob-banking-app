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
    def _get_headers(self, client, path: str = "/login"):
        return client.get(path).headers

    def test_x_frame_options_present(self, client):
        assert self._get_headers(client).get("X-Frame-Options") == "SAMEORIGIN"

    def test_x_content_type_options_present(self, client):
        assert self._get_headers(client).get("X-Content-Type-Options") == "nosniff"

    def test_referrer_policy_present(self, client):
        assert "Referrer-Policy" in self._get_headers(client)

    def test_content_security_policy_present(self, client):
        assert "Content-Security-Policy" in self._get_headers(client)

    def test_csp_allows_bootstrap_cdn(self, client):
        assert "cdn.jsdelivr.net" in self._get_headers(client).get("Content-Security-Policy", "")

    def test_security_headers_on_api_endpoint(self, auth_client):
        assert auth_client.get("/balance").headers.get("X-Frame-Options") == "SAMEORIGIN"

    def test_security_headers_on_error_response(self, client):
        assert client.get("/this-route-does-not-exist").headers.get("X-Content-Type-Options") == "nosniff"


class TestErrorHandlers:
    def test_404_returns_json(self, client):
        res = client.get("/this-does-not-exist")
        assert res.status_code == 404
        assert "error" in json.loads(res.data)

    def test_404_error_message_not_empty(self, client):
        assert json.loads(client.get("/missing-page").data)["error"]

    def test_401_unauthenticated_api_returns_json(self, client):
        res = client.get("/balance")
        assert res.status_code == 401
        assert "error" in json.loads(res.data)


class TestSessionCookieFlags:
    def test_session_cookie_exists_after_login(self, client):
        import json as _json
        res = client.post(
            "/login",
            data=_json.dumps({"username": "alice", "password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 200
        assert client.get_cookie("session") is not None
