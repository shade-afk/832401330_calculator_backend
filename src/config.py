"""Application configuration.

All values can be overridden through environment variables so that the same
code runs unchanged in development and in production.
"""

import os


class Config:
    """Runtime configuration for the calculator backend."""

    # HTTP server
    # ``PORT`` is injected by most cloud platforms (Render, Railway, ...),
    # while ``CALC_PORT`` overrides it for local development.
    HOST: str = os.environ.get("CALC_HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("CALC_PORT") or os.environ.get("PORT", "5000"))
    DEBUG: bool = os.environ.get("CALC_DEBUG", "1") == "1"

    # SQLite database file (created automatically on first run)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH: str = os.environ.get(
        "CALC_DB_PATH",
        os.path.join(BASE_DIR, "data", "calculator.db"),
    )

    # CORS: allow the separated front end to call the API.
    # "*" is fine for local development; restrict it in production if needed.
    CORS_ORIGINS: str = os.environ.get("CALC_CORS_ORIGINS", "*")

    # Maximum number of history rows returned by a single list request.
    HISTORY_LIMIT: int = int(os.environ.get("CALC_HISTORY_LIMIT", "200"))
