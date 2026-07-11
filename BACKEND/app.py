"""
app.py — Application factory.

The module-level ``app`` global is kept for backward compatibility
(``python app.py`` still works), but all real wiring happens inside
``create_app()`` so that tests can spin up isolated instances with
different config objects.

Usage:
    # Run the development server
    cd BACKEND && source venv/bin/activate && python app.py

    # Import the factory in tests
    from app import create_app
    from config import TestingConfig
    flask_app = create_app(TestingConfig)
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Type

from dotenv import load_dotenv
from flask import Flask

from config import BaseConfig, CONFIG_MAP, DevelopmentConfig
from models import init_db

# Load .env (project root or BACKEND/) before anything else reads os.environ.
# load_dotenv is a no-op when the file does not exist, so it is safe in CI.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def _configure_logging(log_level: str) -> None:
    """Configure root logger with a consistent format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def create_app(
    config: Optional[Type[BaseConfig]] = None,
) -> Flask:
    """
    Application factory.

    Args:
        config: A BaseConfig subclass.  Defaults to DevelopmentConfig or the
                class named by the FLASK_ENV environment variable.

    Returns:
        A configured, ready-to-use Flask application instance.
    """
    if config is None:
        env_name = os.environ.get("FLASK_ENV", "development")
        config = CONFIG_MAP.get(env_name, DevelopmentConfig)

    flask_app = Flask(__name__, static_folder=None)
    flask_app.config.from_object(config)

    _configure_logging(flask_app.config["LOG_LEVEL"])
    logger = logging.getLogger(__name__)
    logger.debug("create_app: config=%s", config.__name__)

    from routes import banking_bp  # noqa: PLC0415
    flask_app.register_blueprint(banking_bp)

    from routes import register_error_handlers  # noqa: PLC0415
    register_error_handlers(flask_app)

    with flask_app.app_context():
        init_db(flask_app.config["DATABASE"])

    logger.info("Banking application started (env=%s)", config.__name__)
    return flask_app


# ---------------------------------------------------------------------------
# Backward-compatible module-level app for `python app.py`
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=5000)
