"""
routes.py — URL routing and HTTP layer.

Design rules:
  - All routes are registered on a Flask Blueprint (``banking_bp``).
  - Routes only handle HTTP concerns: parse input, call a service, return a response.
  - Every protected route calls ``_auth_guard()``, which returns 401 JSON
    (for API routes) or a redirect (for page routes) when the session is absent.
  - All JSON error responses use the shape ``{"error": "message text"}``.
  - HTML pages are served from FRONTEND/ via ``send_from_directory``.
  - Security headers are added to every response via ``@banking_bp.after_request``.
"""

from __future__ import annotations

import logging
import os

from flask import (
    Blueprint,
    Flask,
    current_app,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)

from services import authenticate, fetch_balance, process_deposit, process_withdrawal

logger = logging.getLogger(__name__)

banking_bp = Blueprint("banking", __name__)


@banking_bp.after_request
def set_security_headers(response):  # type: ignore[return]
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response


def _db() -> str:
    return current_app.config["DATABASE"]  # type: ignore[return-value]


def _frontend() -> str:
    return current_app.config["FRONTEND_DIR"]  # type: ignore[return-value]


def _auth_guard_api():
    if not session.get("user_id"):
        return jsonify({"error": "Authentication required"}), 401
    return None


def _auth_guard_page():
    if not session.get("user_id"):
        return redirect(url_for("banking.login_page"))
    return None


@banking_bp.route("/")
def index():
    return redirect(url_for("banking.login_page"))


@banking_bp.route("/login", methods=["GET"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("banking.dashboard_page"))
    return send_from_directory(_frontend(), "login.html")


@banking_bp.route("/login", methods=["POST"])
def login_action():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    result = authenticate(_db(), username, password)
    if not result.ok:
        logger.info("login_action: failed attempt username=%s", username)
        return jsonify({"error": result.error}), 401

    session["user_id"] = result.id
    session["username"] = result.name
    logger.info("login_action: success username=%s", username)
    return jsonify({"message": "Login successful"}), 200


@banking_bp.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    logger.info("logout: username=%s", username)
    return redirect(url_for("banking.login_page"))


@banking_bp.route("/dashboard")
def dashboard_page():
    guard = _auth_guard_page()
    if guard:
        return guard
    return send_from_directory(_frontend(), "dashboard.html")


@banking_bp.route("/balance")
def balance():
    guard = _auth_guard_api()
    if guard:
        return guard

    result = fetch_balance(_db(), session["user_id"])  # type: ignore[arg-type]
    if not result.ok:
        return jsonify({"error": result.error}), 404

    return jsonify({"balance": result.balance, "username": session.get("username", "")}), 200


@banking_bp.route("/deposit", methods=["GET"])
def deposit_page():
    guard = _auth_guard_page()
    if guard:
        return guard
    return send_from_directory(_frontend(), "deposit.html")


@banking_bp.route("/deposit", methods=["POST"])
def deposit():
    guard = _auth_guard_api()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    result = process_deposit(_db(), session["user_id"], amount)  # type: ignore[arg-type]
    if not result.ok:
        return jsonify({"error": result.error}), 400

    return jsonify({"balance": result.balance}), 200


@banking_bp.route("/withdraw", methods=["GET"])
def withdraw_page():
    guard = _auth_guard_page()
    if guard:
        return guard
    return send_from_directory(_frontend(), "withdraw.html")


@banking_bp.route("/withdraw", methods=["POST"])
def withdraw():
    guard = _auth_guard_api()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    # Validation check 1: amount field must not be empty
    if amount is None or str(amount).strip() == "":
        return jsonify({"error": "Amount is required"}), 400

    # Validation check 2: amount must be a positive number
    try:
        amount_float = float(amount)
    except (TypeError, ValueError):
        amount_float = None
    if amount_float is None or amount_float <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400

    # Validation check 3: amount must not exceed the current balance
    balance_result = fetch_balance(_db(), session["user_id"])  # type: ignore[arg-type]
    if balance_result.ok and amount_float > balance_result.balance:
        return jsonify({"error": "Insufficient funds"}), 422

    result = process_withdrawal(_db(), session["user_id"], amount)  # type: ignore[arg-type]
    if not result.ok:
        status = 422 if result.error == "Insufficient balance" else 400
        return jsonify({"error": result.error}), status

    return jsonify({"balance": result.balance}), 200


@banking_bp.route("/static/<path:filename>")
def static_files(filename: str):
    static_dir = os.path.join(_frontend(), "static")
    return send_from_directory(static_dir, filename)


def _add_security_headers(response):
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        ),
    )
    return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(exc):
        logger.warning("400 Bad Request: %s", exc)
        return _add_security_headers(jsonify({"error": "Bad request"})), 400

    @app.errorhandler(401)
    def unauthorized(exc):
        return _add_security_headers(jsonify({"error": "Authentication required"})), 401

    @app.errorhandler(404)
    def not_found(exc):
        logger.info("404 Not Found: %s", request.path)
        return _add_security_headers(jsonify({"error": "Resource not found"})), 404

    @app.errorhandler(500)
    def internal_error(exc):
        logger.exception("500 Internal Server Error")
        return _add_security_headers(jsonify({"error": "An unexpected error occurred"})), 500
