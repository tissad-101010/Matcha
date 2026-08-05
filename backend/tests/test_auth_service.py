"""Authentication business-rule tests independent from HTTP."""

from uuid import UUID

import pytest

from app.auth.passwords import hash_password
from app.auth.repository import LoginAccount
from app.auth.service import InvalidCredentialsError, authenticate


def test_pending_account_cannot_authenticate(monkeypatch) -> None:
    account = LoginAccount(
        UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a"),
        "pending_user",
        "Ada",
        hash_password("Orbite-7-Nébuleuse!"),
        "pending_verification",
        False,
        False,
        False,
    )
    monkeypatch.setattr("app.auth.service.find_account_for_login", lambda _url, _user: account)

    with pytest.raises(InvalidCredentialsError):
        authenticate({"DATABASE_URL": "unused"}, "pending_user", "Orbite-7-Nébuleuse!")


def test_unknown_account_uses_the_same_credentials_error(monkeypatch) -> None:
    monkeypatch.setattr("app.auth.service.find_account_for_login", lambda _url, _user: None)

    with pytest.raises(InvalidCredentialsError):
        authenticate({"DATABASE_URL": "unused"}, "unknown", "incorrect")
