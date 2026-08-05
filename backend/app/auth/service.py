"""Authentication use cases independent from Flask request handling."""

import smtplib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.auth.passwords import hash_password, verify_password
from app.auth.repository import (
    ActivatedAccount,
    LoginAccount,
    activate_pending_account,
    create_pending_account,
    find_account_for_login,
    record_login,
)
from app.auth.tokens import create_token, token_hash
from app.auth.validation import RegisterData
from app.email import send_verification_email

DUMMY_PASSWORD_HASH = hash_password("Valeur-Factice-7!")


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


def verify_email(config: Mapping[str, Any], raw_token: str) -> ActivatedAccount:
    """Activate the account identified by an opaque single-use token."""
    return activate_pending_account(str(config["DATABASE_URL"]), token_hash(raw_token))


class InvalidCredentialsError(ValueError):
    """Hide absent, inactive and incorrect accounts behind one public error."""


def authenticate(config: Mapping[str, Any], username: str, password: str) -> LoginAccount:
    """Authenticate an active local account and record its successful login."""
    database_url = str(config["DATABASE_URL"])
    account = find_account_for_login(database_url, username)
    password_hash = account.password_hash if account else DUMMY_PASSWORD_HASH
    valid_password = verify_password(password_hash, password)
    if account is None or not valid_password or account.status != "active":
        raise InvalidCredentialsError
    record_login(database_url, account.account_id)
    return account
