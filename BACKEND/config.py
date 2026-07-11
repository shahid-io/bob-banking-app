"""
config.py — Application configuration hierarchy.

Configuration is loaded in this order (later values win):
  1. BaseConfig defaults (safe for all environments)
  2. Environment-specific subclass overrides
  3. Values read from a .env file via python-dotenv

Usage in create_app():
    from config import DevelopmentConfig
    app = create_app(DevelopmentConfig)

Environment variable reference: see .env.example
"""

from __future__ import annotations

import os
from pathlib import Path

# Project layout constants
_BASE_DIR: Path = Path(__file__).resolve().parent          # BACKEND/
_FRONTEND_DIR: Path = _BASE_DIR.parent / "FRONTEND"        # FRONTEND/
_DEFAULT_DB: Path = _BASE_DIR / "banking.db"               # BACKEND/banking.db


class BaseConfig:
    """
    Shared defaults.  Never instantiate this directly — use a subclass.
    All settings that are common to every environment live here.
    """

    # ------------------------------------------------------------------
    # Flask core
    # ------------------------------------------------------------------
    # SECRET_KEY MUST be overridden by an environment variable in production.
    # The fallback value here is only safe for local development.
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-replace-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # ------------------------------------------------------------------
    # Session cookie security
    # ------------------------------------------------------------------
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    # Set to True when the app is served over HTTPS (i.e. production)
    SESSION_COOKIE_SECURE: bool = False

    # ------------------------------------------------------------------
    # Application paths
    # ------------------------------------------------------------------
    # Treat an empty DATABASE_URL the same as a missing one so that a blank
    # line in .env never overrides the local default path.
    DATABASE: str = os.environ.get("DATABASE_URL") or str(_DEFAULT_DB)
    FRONTEND_DIR: str = str(_FRONTEND_DIR)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # ------------------------------------------------------------------
    # Demo seed data — used by init_db to populate the database
    # ------------------------------------------------------------------
    SEED_DEMO_ACCOUNTS: bool = True


class DevelopmentConfig(BaseConfig):
    """
    Local development.  Debug mode on, verbose logging.
    Never run this in production.
    """

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class TestingConfig(BaseConfig):
    """
    pytest / CI.  Uses an in-process temporary database supplied by the
    test fixture, never the real banking.db.
    """

    TESTING: bool = True
    DEBUG: bool = False
    # Disable secure-only cookie so the test client (HTTP, not HTTPS) works
    SESSION_COOKIE_SECURE: bool = False
    # DATABASE will be overridden per-test by the conftest fixture
    DATABASE: str = ":memory:"
    LOG_LEVEL: str = "WARNING"


class ProductionConfig(BaseConfig):
    """
    Production.  All secrets come from environment variables — no defaults.
    The application will raise at startup if mandatory vars are missing.
    """

    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "WARNING")

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

    @classmethod
    def validate(cls) -> None:
        """
        Call at app startup in production to fail fast if required env vars
        are absent.  Raises RuntimeError listing every missing variable.
        """
        required = {"SECRET_KEY", "DATABASE_URL"}
        missing = {k for k in required if not os.environ.get(k)}
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(sorted(missing))}"
            )


# ------------------------------------------------------------------
# Config registry — used by create_app to resolve string names
# ------------------------------------------------------------------
CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
