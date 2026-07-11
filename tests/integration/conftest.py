"""
tests/integration/conftest.py

Shared pytest fixtures for integration tests.

Uses the ``create_app`` factory with ``TestingConfig`` so every test gets a
clean, isolated Flask application instance pointed at a fresh temporary
database.  The database file is cleaned up automatically by pytest's
``tmp_path`` fixture.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

# Ensure BACKEND/ is on sys.path so Flask app and models can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "BACKEND"))

from app import create_app
from config import TestingConfig
from models import init_db


@pytest.fixture
def app(tmp_path):
    """
    Create a fully isolated Flask test application.

    - Pointed at a temporary SQLite database seeded with demo accounts.
    - Database file is auto-removed when the test finishes (tmp_path scope).
    """
    db_file = str(tmp_path / "test_banking.db")

    # Override DATABASE before creating the app so init_db uses the test file
    TestingConfig.DATABASE = db_file  # type: ignore[assignment]
    flask_app = create_app(TestingConfig)

    # Ensure the test db is populated (init_db is called inside create_app,
    # but we set DATABASE after building the default config object, so
    # we seed again to be safe for the override path)
    init_db(db_file)
    flask_app.config["DATABASE"] = db_file

    yield flask_app


@pytest.fixture
def client(app):
    """A test client that maintains cookies (required for Flask sessions)."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A test client already authenticated as alice."""
    client.post(
        "/login",
        data=json.dumps({"username": "alice", "password": "password123"}),
        content_type="application/json",
    )
    return client
