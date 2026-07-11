"""
tests/integration/test_routes.py

Integration tests for all Flask routes.
"""

import json


class TestLogin:
    def test_get_login_returns_html_page(self, client):
        res = client.get("/login")
        assert res.status_code == 200
        assert b"SecureBank" in res.data or b"login" in res.data.lower()

    def test_post_valid_credentials_returns_200(self, client):
        res = client.post("/login", data=json.dumps({"username": "alice", "password": "password123"}), content_type="application/json")
        assert res.status_code == 200

    def test_post_valid_credentials_sets_session(self, client):
        client.post("/login", data=json.dumps({"username": "alice", "password": "password123"}), content_type="application/json")
        assert client.get("/balance").status_code == 200

    def test_post_invalid_password_returns_401(self, client):
        res = client.post("/login", data=json.dumps({"username": "alice", "password": "wrong"}), content_type="application/json")
        assert res.status_code == 401

    def test_post_unknown_username_returns_401(self, client):
        res = client.post("/login", data=json.dumps({"username": "nobody", "password": "password123"}), content_type="application/json")
        assert res.status_code == 401

    def test_post_invalid_credentials_error_shape(self, client):
        res = client.post("/login", data=json.dumps({"username": "alice", "password": "wrong"}), content_type="application/json")
        assert "error" in json.loads(res.data)

    def test_post_empty_body_returns_401(self, client):
        res = client.post("/login", data=json.dumps({}), content_type="application/json")
        assert res.status_code == 401


class TestLogout:
    def test_logout_clears_session(self, auth_client):
        assert auth_client.get("/balance").status_code == 200
        auth_client.get("/logout")
        assert auth_client.get("/balance").status_code == 401


class TestBalance:
    def test_authenticated_request_returns_200(self, auth_client):
        assert auth_client.get("/balance").status_code == 200

    def test_unauthenticated_request_returns_401(self, client):
        assert client.get("/balance").status_code == 401

    def test_response_contains_numeric_balance(self, auth_client):
        data = json.loads(auth_client.get("/balance").data)
        assert "balance" in data
        assert data["balance"] == 1000.00

    def test_response_contains_username(self, auth_client):
        assert "username" in json.loads(auth_client.get("/balance").data)


class TestDeposit:
    def test_valid_deposit_returns_200(self, auth_client):
        res = auth_client.post("/deposit", data=json.dumps({"amount": 500}), content_type="application/json")
        assert res.status_code == 200

    def test_valid_deposit_returns_correct_new_balance(self, auth_client):
        data = json.loads(auth_client.post("/deposit", data=json.dumps({"amount": 500}), content_type="application/json").data)
        assert data["balance"] == 1500.00

    def test_zero_amount_returns_400(self, auth_client):
        assert auth_client.post("/deposit", data=json.dumps({"amount": 0}), content_type="application/json").status_code == 400

    def test_negative_amount_returns_400(self, auth_client):
        assert auth_client.post("/deposit", data=json.dumps({"amount": -100}), content_type="application/json").status_code == 400

    def test_non_numeric_amount_returns_400(self, auth_client):
        assert auth_client.post("/deposit", data=json.dumps({"amount": "abc"}), content_type="application/json").status_code == 400

    def test_unauthenticated_deposit_returns_401(self, client):
        assert client.post("/deposit", data=json.dumps({"amount": 100}), content_type="application/json").status_code == 401

    def test_error_response_shape(self, auth_client):
        res = auth_client.post("/deposit", data=json.dumps({"amount": -1}), content_type="application/json")
        assert "error" in json.loads(res.data)


class TestWithdraw:
    def test_valid_withdrawal_returns_200(self, auth_client):
        assert auth_client.post("/withdraw", data=json.dumps({"amount": 200}), content_type="application/json").status_code == 200

    def test_valid_withdrawal_returns_correct_new_balance(self, auth_client):
        data = json.loads(auth_client.post("/withdraw", data=json.dumps({"amount": 200}), content_type="application/json").data)
        assert data["balance"] == 800.00

    def test_exceeding_balance_returns_422(self, auth_client):
        assert auth_client.post("/withdraw", data=json.dumps({"amount": 9999}), content_type="application/json").status_code == 422

    def test_exceeding_balance_error_message(self, auth_client):
        data = json.loads(auth_client.post("/withdraw", data=json.dumps({"amount": 9999}), content_type="application/json").data)
        assert data["error"] == "Insufficient balance"

    def test_zero_amount_returns_400(self, auth_client):
        assert auth_client.post("/withdraw", data=json.dumps({"amount": 0}), content_type="application/json").status_code == 400

    def test_negative_amount_returns_400(self, auth_client):
        assert auth_client.post("/withdraw", data=json.dumps({"amount": -50}), content_type="application/json").status_code == 400

    def test_unauthenticated_withdrawal_returns_401(self, client):
        assert client.post("/withdraw", data=json.dumps({"amount": 100}), content_type="application/json").status_code == 401

    def test_session_cleared_after_logout_blocks_withdraw(self, auth_client):
        auth_client.get("/logout")
        assert auth_client.post("/withdraw", data=json.dumps({"amount": 50}), content_type="application/json").status_code == 401


class TestPageRoutes:
    def test_root_redirects_to_login(self, client):
        res = client.get("/")
        assert res.status_code == 302
        assert "/login" in res.headers.get("Location", "")

    def test_dashboard_unauthenticated_redirects_to_login(self, client):
        assert client.get("/dashboard").status_code == 302

    def test_dashboard_authenticated_returns_html(self, auth_client):
        res = auth_client.get("/dashboard")
        assert res.status_code == 200
        assert b"SecureBank" in res.data

    def test_deposit_page_unauthenticated_redirects(self, client):
        assert client.get("/deposit").status_code == 302

    def test_withdraw_page_unauthenticated_redirects(self, client):
        assert client.get("/withdraw").status_code == 302

    def test_deposit_page_authenticated_returns_html(self, auth_client):
        res = auth_client.get("/deposit")
        assert res.status_code == 200
        assert b"Deposit" in res.data

    def test_withdraw_page_authenticated_returns_html(self, auth_client):
        res = auth_client.get("/withdraw")
        assert res.status_code == 200
        assert b"Withdraw" in res.data
