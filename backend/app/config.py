"""Explicit environment parsing for application configuration."""

import os
from datetime import timedelta


def _boolean(name: str, default: bool) -> bool:
    """Read a boolean without accepting ambiguous values."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def build_config() -> dict[str, object]:
    """Build Flask configuration from environment variables.

    Defaults support local development only. Production validation is performed by the
    configuration check before the service starts.
    """
    environment = os.getenv("APP_ENV", "development")
    secure_cookie = environment == "production"
    valkey_url = os.getenv("VALKEY_URL", "redis://:matcha-local@valkey:6379/0")

    return {
        "APP_ENV": environment,
        "SECRET_KEY": os.getenv("SECRET_KEY", "local-only-change-me"),
        "DATABASE_URL": os.getenv(
            "DATABASE_URL",
            "postgresql://matcha:matcha-local@postgres:5432/matcha",
        ),
        "VALKEY_URL": valkey_url,
        "SESSION_TYPE": "redis",
        "SESSION_REDIS_URL": valkey_url,
        "SESSION_KEY_PREFIX": "matcha:session:",
        "SESSION_PERMANENT": True,
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SECURE": secure_cookie,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_NAME": "matcha_session",
        "SOCKET_MESSAGE_QUEUE": valkey_url,
        "S3_ENDPOINT_URL": os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
        "S3_REGION": os.getenv("S3_REGION", "us-east-1"),
        "S3_ACCESS_KEY": os.getenv("S3_ACCESS_KEY", "matcha-local"),
        "S3_SECRET_KEY": os.getenv("S3_SECRET_KEY", "local-only-change-me"),
        "S3_BUCKETS": ("profile-photos", "gallery", "temporary"),
        "SMTP_HOST": os.getenv("SMTP_HOST", "mailpit"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", "1025")),
        "SMTP_USERNAME": os.getenv("SMTP_USERNAME", ""),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
        "SMTP_USE_TLS": _boolean("SMTP_USE_TLS", False),
        "SMTP_FROM_EMAIL": os.getenv("SMTP_FROM_EMAIL", "matcha@example.test"),
        "SMTP_FROM_NAME": os.getenv("SMTP_FROM_NAME", "Matcha"),
        "FRONTEND_URL": os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "CONSENT_POLICY_VERSION": os.getenv("CONSENT_POLICY_VERSION", "2026-08"),
        "JSON_SORT_KEYS": False,
        "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
        "TESTING": _boolean("TESTING", False),
    }
