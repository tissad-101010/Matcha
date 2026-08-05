"""Authentication use cases independent from Flask request handling."""

import smtplib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.auth.passwords import hash_password
from app.auth.repository import create_pending_account
from app.auth.tokens import create_token
from app.auth.validation import RegisterData
from app.email import send_verification_email


@dataclass(frozen=True)
class RegistrationResult:
    """Public result documented by the API transfer models."""

    account_id: UUID
    verification_email_sent: bool


def register(config: Mapping[str, Any], data: RegisterData) -> RegistrationResult:
    """Persist a pending account, then send its single-use verification link."""
    raw_token, verification_hash = create_token()
    pending = create_pending_account(
        str(config["DATABASE_URL"]), data, hash_password(data.password), verification_hash
    )
    try:
        send_verification_email(config, data.email, raw_token)
    except (OSError, smtplib.SMTPException):
        return RegistrationResult(pending.account_id, False)
    return RegistrationResult(pending.account_id, True)
