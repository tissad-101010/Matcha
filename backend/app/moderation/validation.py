"""Validation for immutable profile reports."""

from typing import Any

from app.auth.validation import InputValidationError

REPORT_REASONS = {
    "fake_profile",
    "inappropriate_content",
    "harassment",
    "spam",
    "underage",
    "other",
}


def validate_report(payload: Any) -> tuple[str, str | None]:
    """Return a controlled reason and a normalized optional description."""
    if not isinstance(payload, dict):
        raise InputValidationError({"body": "Un objet JSON est requis."})
    reason = payload.get("reason")
    description = payload.get("description")
    fields: dict[str, str] = {}
    if reason not in REPORT_REASONS:
        fields["reason"] = "Choisissez un motif valide."
    if description is not None:
        if not isinstance(description, str):
            fields["description"] = "La description doit être du texte."
        else:
            description = " ".join(description.split())
            if not 1 <= len(description) <= 1000:
                fields["description"] = "La description doit contenir entre 1 et 1000 caractères."
    if fields:
        raise InputValidationError(fields)
    return str(reason), description
