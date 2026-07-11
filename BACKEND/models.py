"""
models.py — Database access layer.

Design rules:
  - Every public function accepts ``db_path`` as its first argument so that
    tests can pass a temporary file path without touching the real database.
  - All functions open their own connection, execute, commit (writes), then
    close — connection lifetimes are kept as short as possible.
  - ``sqlite3.Row`` row_factory is used so rows are addressable by column name.
  - CHECK constraints and an index on ``username`` are added to the DDL so the
    database itself enforces invariants, not just application code.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Optional

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _connect(db_path: str) -> sqlite3.Connection:
    """Return a new connection with ``sqlite3.Row`` factory and FK enforcement."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema & seed
# ---------------------------------------------------------------------------

_DDL = """
    CREATE TABLE IF NOT EXISTS customers (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name     TEXT    NOT NULL,
        username      TEXT    NOT NULL UNIQUE,
        password_hash TEXT    NOT NULL,
        balance       REAL    NOT NULL DEFAULT 0.0
                               CHECK (balance >= 0.0)
    );
"""

_SEED_ACCOUNTS: tuple[tuple[str, str, str, float], ...] = (
    ("Alice Johnson", "alice", "password123", 1000.00),
    ("Bob Williams",  "bob",   "password456", 1500.00),
    ("Carol Davis",   "carol", "password789", 2000.00),
)


def init_db(db_path: str) -> None:
    """
    Create the schema if it does not exist, then seed demo accounts when the
    table is empty.  Safe to call on every application startup (idempotent).

    Args:
        db_path: Filesystem path to the SQLite database file.
                 Use ``:memory:`` for in-process testing only.
    """
    logger.debug("init_db: path=%s", db_path)
    conn = _connect(db_path)
    try:
        conn.execute(_DDL)
        # Index on username speeds up the login lookup
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_customers_username "
            "ON customers (username)"
        )
        conn.commit()

        row = conn.execute("SELECT COUNT(*) AS cnt FROM customers").fetchone()
        if row["cnt"] == 0:
            logger.info("init_db: seeding %d demo accounts", len(_SEED_ACCOUNTS))
            for full_name, username, password, balance in _SEED_ACCOUNTS:
                conn.execute(
                    "INSERT INTO customers "
                    "(full_name, username, password_hash, balance) "
                    "VALUES (?, ?, ?, ?)",
                    (full_name, username, generate_password_hash(password), balance),
                )
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def get_customer_by_username(
    db_path: str, username: str
) -> Optional[dict[str, object]]:
    """
    Return the customer record for *username*, or ``None`` if not found.

    The returned dict contains: id, full_name, username, password_hash, balance.
    """
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, full_name, username, password_hash, balance "
            "FROM customers WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_balance(db_path: str, customer_id: int) -> Optional[float]:
    """
    Return the current balance for *customer_id*, or ``None`` if not found.
    """
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT balance FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        return float(row["balance"]) if row else None
    finally:
        conn.close()


def update_balance(db_path: str, customer_id: int, new_balance: float) -> None:
    """
    Overwrite the stored balance for *customer_id*.

    The ``CHECK (balance >= 0)`` constraint on the table is the last line of
    defence, but callers (services.py) must validate before calling this.
    """
    logger.debug(
        "update_balance: customer_id=%s new_balance=%.2f", customer_id, new_balance
    )
    conn = _connect(db_path)
    try:
        conn.execute(
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id),
        )
        conn.commit()
    finally:
        conn.close()
