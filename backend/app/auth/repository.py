"""SQL operations needed by authentication use cases."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg
from psycopg.errors import UniqueViolation

from app.auth.validation import RegisterData


@dataclass(frozen=True)
class PendingRegistration:
    """Identifiers produced by the atomic registration transaction."""

    account_id: UUID


@dataclass(frozen=True)
class ActivatedAccount:
    """Public account state returned after successful verification."""

    account_id: UUID
    username: str
    first_name: str


@dataclass(frozen=True)
class LoginAccount:
    """Minimal private account record required to establish a session."""

    account_id: UUID
    username: str
    first_name: str
    password_hash: str
    status: str
    profile_complete: bool
    has_main_photo: bool
    matching_enabled: bool


class DuplicateAccountError(ValueError):
    """Report a public field conflict without leaking SQL details."""

    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


class InvalidTokenError(ValueError):
    """Represent every invalid, expired or consumed token identically."""


def create_pending_account(
    database_url: str, data: RegisterData, password_hash: str, verification_hash: bytes
) -> PendingRegistration:
    """Create the account, its initial profile and verification token atomically."""
    try:
        with psycopg.connect(database_url) as connection:
            account_id = connection.execute(
                """
                INSERT INTO accounts (email, username, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (data.email, data.username, password_hash),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO profiles (user_id, first_name, last_name, birth_date)
                VALUES (%s, %s, %s, %s)
                """,
                (account_id, data.first_name, data.last_name, data.birth_date),
            )
            connection.execute(
                """
                INSERT INTO account_tokens (account_id, type, token_hash, expires_at)
                VALUES (%s, 'verify_email', %s, %s)
                """,
                (account_id, verification_hash, datetime.now(UTC) + timedelta(hours=24)),
            )
        return PendingRegistration(account_id)
    except UniqueViolation as error:
        constraint = error.diag.constraint_name or ""
        field = "email" if "email" in constraint else "username"
        raise DuplicateAccountError(field) from error


def activate_pending_account(database_url: str, verification_hash: bytes) -> ActivatedAccount:
    """Consume a valid token and activate its account in one transaction."""
    with psycopg.connect(database_url) as connection:
        token_row = connection.execute(
            """
            SELECT token.id, token.account_id
            FROM account_tokens AS token
            JOIN accounts AS account ON account.id = token.account_id
            WHERE token.token_hash = %s
              AND token.type = 'verify_email'
              AND token.consumed_at IS NULL
              AND token.expires_at > CURRENT_TIMESTAMP
              AND account.status = 'pending_verification'
            FOR UPDATE OF token, account
            """,
            (verification_hash,),
        ).fetchone()
        if token_row is None:
            raise InvalidTokenError

        token_id, account_id = token_row
        connection.execute(
            "UPDATE account_tokens SET consumed_at = CURRENT_TIMESTAMP WHERE id = %s",
            (token_id,),
        )
        account = connection.execute(
            """
            UPDATE accounts
            SET status = 'active', email_verified_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING username
            """,
            (account_id,),
        ).fetchone()
        first_name = connection.execute(
            "SELECT first_name FROM profiles WHERE user_id = %s", (account_id,)
        ).fetchone()[0]
    return ActivatedAccount(account_id, account[0], first_name)


def find_account_for_login(database_url: str, username: str) -> LoginAccount | None:
    """Load only fields needed for authentication and the SessionUser response."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT account.id, account.username, profile.first_name,
                   account.password_hash, account.status,
                   (profile.gender IS NOT NULL AND profile.bio IS NOT NULL
                    AND EXISTS (SELECT 1 FROM profile_tags WHERE user_id = account.id)
                    AND EXISTS (
                        SELECT 1 FROM user_locations WHERE user_id = account.id
                    )) AS complete,
                   EXISTS (
                       SELECT 1 FROM photos WHERE user_id = account.id AND is_main
                   ) AS has_photo,
                   COALESCE((
                       SELECT granted FROM consent_events
                       WHERE user_id = account.id AND purpose = 'matching_preferences'
                       ORDER BY occurred_at DESC, id DESC LIMIT 1
                   ), false) AS matching_enabled
            FROM accounts AS account
            JOIN profiles AS profile ON profile.user_id = account.id
            WHERE account.username = %s
            """,
            (username,),
        ).fetchone()
    return LoginAccount(*row) if row else None


def record_login(database_url: str, account_id: UUID) -> None:
    """Persist the last successful login required by the subject's presence display."""
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "UPDATE accounts SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s", (account_id,)
        )
