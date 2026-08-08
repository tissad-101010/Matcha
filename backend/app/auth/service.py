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
    consume_password_reset,
    create_password_reset,
    create_pending_account,
    find_account_for_login,
    record_login,
    replace_verification_token,
)
from app.auth.tokens import create_token, token_hash
from app.auth.validation import RegisterData
from app.email import send_password_reset_email, send_verification_email

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


def request_password_reset(config: Mapping[str, Any], email: str) -> None:
    """Create and e-mail a reset token while keeping unknown accounts indistinguishable."""
    raw_token, reset_hash = create_token()
    recipient = create_password_reset(str(config["DATABASE_URL"]), email, reset_hash)
    if recipient is None:
        return
    try:
        send_password_reset_email(config, recipient, raw_token)
    except (OSError, smtplib.SMTPException):
        return


def reset_password(config: Mapping[str, Any], raw_token: str, new_password: str) -> None:
    """Consume a reset token and rotate the password and session version atomically."""
    consume_password_reset(
        str(config["DATABASE_URL"]), token_hash(raw_token), hash_password(new_password)
    )


def resend_verification(config: Mapping[str, Any], email: str) -> None:
    """Replace and send a verification token while returning no account information."""
    raw_token, verification_hash = create_token()
    recipient = replace_verification_token(
        str(config["DATABASE_URL"]), email, verification_hash
    )
    if recipient is None:
        return
    try:
        send_verification_email(config, recipient, raw_token)
    except (OSError, smtplib.SMTPException):
        return
