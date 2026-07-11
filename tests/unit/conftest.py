"""
tests/unit/conftest.py

Shared pytest fixture for unit tests.
Provides a ``db_path`` fixture that yields a fresh, seeded SQLite database
file path.  The file is deleted after every test function.
"""

from __future__ import annotations

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "BACKEND"))

from models import init_db


@pytest.fixture
def db_path():
    """Yield the path to a fresh, seeded SQLite database; delete it after the test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.unlink(path)
