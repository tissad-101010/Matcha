"""Registration transfer-model validation tests."""

from datetime import date

import pytest

from app.auth.validation import (
    InputValidationError,
    validate_login,
    validate_register,
    validate_token,
)

VALID_PAYLOAD = {
    "first_name": "  Alice ",
    "last_name": " Martin ",
    "username": " Alice_42 ",
    "email": " Alice@Example.TEST ",
    "birth_date": "1995-04-12",
    "password": "Rivière-7-Nuages!",
}


def test_register_request_is_normalized() -> None:
    result = validate_register(VALID_PAYLOAD, today=date(2026, 8, 5))

    assert result.first_name == "Alice"
    assert result.username == "alice_42"
    assert result.email == "alice@example.test"
    assert result.birth_date == date(1995, 4, 12)


def test_registration_rejects_user_younger_than_eighteen() -> None:
    payload = {**VALID_PAYLOAD, "birth_date": "2008-08-06"}

    with pytest.raises(InputValidationError) as error:
        validate_register(payload, today=date(2026, 8, 5))

    assert error.value.fields == {"birth_date": "Vous devez avoir au moins 18 ans."}


def test_registration_collects_safe_field_errors() -> None:
    with pytest.raises(InputValidationError) as error:
        validate_register({})

    assert set(error.value.fields) == {
        "first_name",
        "last_name",
        "username",
        "email",
        "birth_date",
        "password",
    }


def test_token_request_requires_an_opaque_string() -> None:
    assert validate_token({"token": "a" * 32}) == "a" * 32

    with pytest.raises(InputValidationError):
        validate_token({"token": "short"})


def test_login_request_normalizes_username() -> None:
    result = validate_login({"username": " Ada_42 ", "password": "secret"})

    assert result.username == "ada_42"
    assert result.password == "secret"
