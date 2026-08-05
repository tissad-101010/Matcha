"""Create opaque authentication tokens and store only their fingerprints."""

import hashlib
import secrets


def create_token() -> tuple[str, bytes]:
    """Return a cryptographically random token and its SHA-256 fingerprint."""
    token = secrets.token_urlsafe(32)
    return token, token_hash(token)


def token_hash(token: str) -> bytes:
    """Fingerprint a token for database lookup without retaining the secret."""
    return hashlib.sha256(token.encode("utf-8")).digest()
