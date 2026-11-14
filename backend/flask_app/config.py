import os
from typing import Any

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> dict[str, Any]:
    """Read all settings from the environment; fail fast on missing required ones."""
    load_dotenv()
    app_env = os.environ.get("APP_ENV", "production").strip().lower()
    is_production = app_env == "production"
    return {
        "APP_ENV": app_env,
        "DEBUG": False if is_production else _flag("FLASK_DEBUG", False),
        "SQLALCHEMY_DATABASE_URI": _required("DATABASE_URL"),
        "JWT_SECRET_KEY": _required("JWT_SECRET_KEY"),
        "COOKIE_SECURE": _flag("COOKIE_SECURE", is_production),
        "ACCESS_TOKEN_MINUTES": int(os.environ.get("ACCESS_TOKEN_MINUTES", "15")),
        "REFRESH_TOKEN_DAYS": int(os.environ.get("REFRESH_TOKEN_DAYS", "7")),
        "ACCESS_COOKIE_NAME": os.environ.get("ACCESS_COOKIE_NAME", "access_token"),
        "REFRESH_COOKIE_NAME": os.environ.get("REFRESH_COOKIE_NAME", "refresh_token"),
    }
