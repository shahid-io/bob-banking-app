"""
tests/integration/conftest.py

Shared pytest fixtures for integration tests.
Uses the create_app factory with TestingConfig so every test gets
a clean, isolated Flask application instance.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "BACKEND"))

from app import create_app
from config import TestingConfig
from models import init_db


@pytest.fixture
def app(tmp_path):
    db_file = str(tmp_path / "test_banking.db")
    TestingConfig.DATABASE = db_file  # type: ignore[assignment]
    flask_app = create_app(TestingConfig)
    init_db(db_file)
    flask_app.config["DATABASE"] = db_file
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post(
        "/login",
        data=json.dumps({"username": "alice", "password": "password123"}),
        content_type="application/json",
    )
    return client
