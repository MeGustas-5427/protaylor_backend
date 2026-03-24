from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def load_env(base_dir: Path, filename: str = ".env") -> None:
    """Load project environment variables from the backend root."""
    load_dotenv(base_dir / filename, override=False)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_database_config(base_dir: Path) -> dict[str, dict[str, object]]:
    """Build Django DATABASES from DATABASE_URL or explicit DB_* variables."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme in {"postgres", "postgresql", "psql"}:
            return {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": parsed.path.lstrip("/"),
                    "USER": parsed.username or "",
                    "PASSWORD": parsed.password or "",
                    "HOST": parsed.hostname or "localhost",
                    "PORT": parsed.port or "5432",
                    "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
                }
            }

    if os.getenv("DB_ENGINE") == "postgres":
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "protaylor"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", ""),
                "HOST": os.getenv("DB_HOST", "localhost"),
                "PORT": os.getenv("DB_PORT", "5432"),
                "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
            }
        }

    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": base_dir / "db.sqlite3",
        }
    }
