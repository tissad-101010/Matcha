"""Explicit validation for authentication transfer models."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.auth.passwords import password_error

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
USERNAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class RegisterData:
    """Normalized fields accepted by the account registration service."""

    first_name: str
    last_name: str
    username: str
    email: str
    birth_date: date
    password: str


@dataclass(frozen=True)
class LoginData:
    """Normalized fields accepted by the classic login service."""

    username: str
    password: str


class InputValidationError(ValueError):
    """Carry field errors that are safe to return to the client."""

    def __init__(self, fields: dict[str, str]) -> None:
        super().__init__("Invalid request fields")
        self.fields = fields


def validate_token(payload: Any) -> str:
    """Validate the generic TokenRequest without interpreting the opaque token."""
    token = payload.get("token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not 20 <= len(token) <= 256:
        raise InputValidationError({"token": "Jeton invalide ou expiré."})
    return token


def validate_login(payload: Any) -> LoginData:
    """Validate the documented LoginRequest without exposing account existence."""
    if not isinstance(payload, dict):
        raise InputValidationError({"body": "Un objet JSON est requis."})
    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not 3 <= len(username.strip()) <= 30:
        raise InputValidationError({"credentials": "Identifiants invalides."})
    if not isinstance(password, str) or not password:
        raise InputValidationError({"credentials": "Identifiants invalides."})
    return LoginData(username.strip().casefold(), password)


def validate_register(payload: Any, today: date | None = None) -> RegisterData:
    """Validate and normalize the documented RegisterRequest model."""
    if not isinstance(payload, dict):
        raise InputValidationError({"body": "Un objet JSON est requis."})

    values = {name: payload.get(name) for name in RegisterData.__dataclass_fields__}
    errors: dict[str, str] = {}
    first_name = _bounded_text(values["first_name"], "first_name", 1, 80, errors)
    last_name = _bounded_text(values["last_name"], "last_name", 1, 80, errors)
    username = _username(values["username"], errors)
    email = _email(values["email"], errors)
    birth_date = _adult_birth_date(values["birth_date"], today or date.today(), errors)
    password = values["password"] if isinstance(values["password"], str) else ""
    policy_error = password_error(password)
    if policy_error:
        errors["password"] = policy_error
    if errors:
        raise InputValidationError(errors)
    return RegisterData(first_name, last_name, username, email, birth_date, password)


def _bounded_text(value: Any, name: str, minimum: int, maximum: int, errors: dict[str, str]) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not minimum <= len(normalized) <= maximum:
        errors[name] = f"Ce champ doit contenir entre {minimum} et {maximum} caractères."
    return normalized


def _username(value: Any, errors: dict[str, str]) -> str:
    username = value.strip().casefold() if isinstance(value, str) else ""
    if not 3 <= len(username) <= 30 or not USERNAME_PATTERN.fullmatch(username):
        errors["username"] = "Utilisez 3 à 30 lettres minuscules, chiffres ou underscores."
    return username


def _email(value: Any, errors: dict[str, str]) -> str:
    email = value.strip().casefold() if isinstance(value, str) else ""
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        errors["email"] = "Adresse e-mail invalide."
    return email


def _adult_birth_date(value: Any, today: date, errors: dict[str, str]) -> date:
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else date.min
    except ValueError:
        parsed = date.min
    try:
        adult_cutoff = today.replace(year=today.year - 18)
    except ValueError:
        adult_cutoff = today.replace(year=today.year - 18, day=28)
    if parsed == date.min or parsed > adult_cutoff:
        errors["birth_date"] = "Vous devez avoir au moins 18 ans."
    return parsed
