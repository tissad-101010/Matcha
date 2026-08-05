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


class DuplicateAccountError(ValueError):
    """Report a public field conflict without leaking SQL details."""

    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


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
