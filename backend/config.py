"""
Application configuration.
Each environment reads from environment variables with safe defaults.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # SQLite by default; override DATABASE_URL for Postgres/MySQL in production
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'expenses.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    TESTING: bool = False
    # Keep JSON keys in insertion order; improves predictability in tests
    JSON_SORT_KEYS: bool = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


CONFIG_MAP: dict[str, type[Config]] = {
    "development": Config,
    "testing": TestingConfig,
    "production": Config,
}


def get_config() -> type[Config]:
    env = os.getenv("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, Config)
