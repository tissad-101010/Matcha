"""HTTP contract tests for authentication routes."""

from uuid import UUID

from flask.testing import FlaskClient

from app.auth.repository import (
    ActivatedAccount,
    DuplicateAccountError,
    InvalidTokenError,
    LoginAccount,
)
from app.auth.service import InvalidCredentialsError, RegistrationResult

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


def test_login_session_and_csrf_protected_logout(client: FlaskClient, monkeypatch) -> None:
    account_id = UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a")
    account = LoginAccount(
        account_id, "ada_lovelace", "Ada", "unused", "active", False, False, False, 0
    )
    monkeypatch.setattr("app.routes.auth.authenticate", lambda _config, _user, _password: account)

    login_response = client.post(
        "/api/v1/auth/login", json={"username": "ada_lovelace", "password": "secret"}
    )
    csrf_token = login_response.get_json()["data"]["csrf_token"]

    assert login_response.status_code == 200
    assert "matcha_session=" in login_response.headers["Set-Cookie"]
    assert "HttpOnly" in login_response.headers["Set-Cookie"]
    assert client.get("/api/v1/auth/session").get_json()["data"]["user"]["id"] == str(account_id)
    assert client.post("/api/v1/auth/logout").status_code == 403
    assert (
        client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token}).status_code
        == 204
    )
    assert client.get("/api/v1/auth/session").status_code == 401


def test_login_uses_one_neutral_credentials_error(client: FlaskClient, monkeypatch) -> None:
    def invalid(_config, _user, _password):
        raise InvalidCredentialsError

    monkeypatch.setattr("app.routes.auth.authenticate", invalid)

    response = client.post(
        "/api/v1/auth/login", json={"username": "unknown", "password": "incorrect"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_forgot_password_response_is_neutral(client: FlaskClient, monkeypatch) -> None:
    requested: list[str] = []
    monkeypatch.setattr(
        "app.routes.auth.request_password_reset",
        lambda _config, email: requested.append(email),
    )

    existing = client.post(
        "/api/v1/auth/forgot-password", json={"email": "member@example.test"}
    )
    invalid = client.post("/api/v1/auth/forgot-password", json={"email": "invalid"})

    assert existing.status_code == invalid.status_code == 200
    assert existing.get_json() == invalid.get_json()
    assert requested == ["member@example.test", "invalid@example.invalid"]


def test_reset_password_returns_no_content(client: FlaskClient, monkeypatch) -> None:
    monkeypatch.setattr("app.routes.auth.reset_password", lambda *_args: None)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "a" * 32, "new_password": "Orbite-7-Nébuleuse!"},
    )

    assert response.status_code == 204
    assert response.data == b""


def test_resend_verification_is_neutral(client: FlaskClient, monkeypatch) -> None:
    monkeypatch.setattr("app.routes.auth.resend_verification", lambda *_args: None)

    known = client.post(
        "/api/v1/auth/resend-verification", json={"email": "member@example.test"}
    )
    invalid = client.post("/api/v1/auth/resend-verification", json={"email": "invalid"})

    assert known.status_code == invalid.status_code == 200
    assert known.get_json() == invalid.get_json()
