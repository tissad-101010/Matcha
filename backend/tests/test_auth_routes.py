"""HTTP contract tests for authentication routes."""

from uuid import UUID

from flask.testing import FlaskClient

from app.auth.repository import ActivatedAccount, DuplicateAccountError, InvalidTokenError
from app.auth.service import RegistrationResult

VALID_REGISTRATION = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "username": "ada_lovelace",
    "email": "ada@example.test",
    "birth_date": "1990-12-10",
    "password": "Orbite-7-Nébuleuse!",
}


def test_register_returns_documented_pending_account(client: FlaskClient, monkeypatch) -> None:
    account_id = UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a")
    monkeypatch.setattr(
        "app.routes.auth.register", lambda _config, _data: RegistrationResult(account_id, True)
    )

    response = client.post("/api/v1/auth/register", json=VALID_REGISTRATION)

    assert response.status_code == 201
    assert response.get_json() == {
        "data": {
            "account_id": str(account_id),
            "status": "pending_verification",
            "verification_email_sent": True,
        }
    }


def test_register_returns_field_validation_errors(client: FlaskClient) -> None:
    response = client.post("/api/v1/auth/register", json={})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    assert "email" in response.get_json()["error"]["fields"]


def test_register_hides_which_identifier_conflicts(client: FlaskClient, monkeypatch) -> None:
    def duplicate(_config, _data):
        raise DuplicateAccountError("email")

    monkeypatch.setattr("app.routes.auth.register", duplicate)

    response = client.post("/api/v1/auth/register", json=VALID_REGISTRATION)

    assert response.status_code == 409
    assert response.get_json()["error"]["message"] == (
        "Cette adresse e-mail ou ce nom d’utilisateur est indisponible."
    )


def test_verify_email_returns_the_documented_session_user(client: FlaskClient, monkeypatch) -> None:
    account_id = UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a")
    monkeypatch.setattr(
        "app.routes.auth.verify_email",
        lambda _config, _token: ActivatedAccount(account_id, "ada_lovelace", "Ada"),
    )

    response = client.post("/api/v1/auth/verify-email", json={"token": "a" * 32})

    assert response.status_code == 200
    assert response.get_json() == {
        "data": {
            "id": str(account_id),
            "username": "ada_lovelace",
            "first_name": "Ada",
            "account_status": "active",
            "profile_complete": False,
            "has_main_photo": False,
            "matching_enabled": False,
        }
    }


def test_verify_email_hides_invalid_token_reason(client: FlaskClient, monkeypatch) -> None:
    def invalid(_config, _token):
        raise InvalidTokenError

    monkeypatch.setattr("app.routes.auth.verify_email", invalid)

    response = client.post("/api/v1/auth/verify-email", json={"token": "a" * 32})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "invalid_token"
