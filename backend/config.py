import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _require_postgres_url(env_key: str) -> str:
    url = (os.getenv(env_key) or "").strip()
    if not url:
        raise RuntimeError(
            f"{env_key} is required. Copy .env.example to .env and set a PostgreSQL URL."
        )
    lowered = url.lower()
    if lowered.startswith("sqlite:"):
        raise RuntimeError("SQLite is not supported. Use PostgreSQL.")
    if not (
        lowered.startswith("postgresql:")
        or lowered.startswith("postgresql+")
        or lowered.startswith("postgres:")
        or lowered.startswith("postgres+")
    ):
        raise RuntimeError(f"{env_key} must be a PostgreSQL connection string.")
    return url


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "facultylink-dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "facultylink-jwt-dev-secret-change-me-32")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def database_url() -> str:
        return _require_postgres_url("DATABASE_URL")

    _upload = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
    UPLOAD_FOLDER = _upload if _upload.is_absolute() else BASE_DIR / _upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    CORS_ORIGINS = [
        origin.strip()
        for origin in (os.getenv("CORS_ORIGINS") or "http://127.0.0.1:8080,http://localhost:8080").split(",")
        if origin.strip()
    ]

    GUIDELINE_LABEL = "DBM–CHED Joint Circular No. 01, s. 2026"

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
    SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "").strip()
    SMTP_FROM = (os.getenv("SMTP_FROM") or SMTP_USER or "").strip()
    WEB_PUBLIC_URL = (os.getenv("WEB_PUBLIC_URL") or "http://127.0.0.1:8080").rstrip("/")
    FORGOT_PASSWORD_RATE_LIMIT = int(os.getenv("FORGOT_PASSWORD_RATE_LIMIT", "8"))
    FORGOT_PASSWORD_RATE_WINDOW_SECONDS = int(os.getenv("FORGOT_PASSWORD_RATE_WINDOW_SECONDS", "3600"))

    @classmethod
    def smtp_enabled(cls) -> bool:
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD and cls.SMTP_FROM)

    @classmethod
    def sqlalchemy_database_uri(cls) -> str:
        return cls.database_url()
