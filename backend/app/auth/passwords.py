"""Password policy and Argon2id hashing in one auditable module."""

import re
import unicodedata
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
WORD_PATTERN = re.compile(r"[a-z]+")
COMMON_WORDS_PATH = Path(__file__).with_name("common_passwords.txt")
HASHER = PasswordHasher()


def password_error(password: str) -> str | None:
    """Return the first policy error without retaining the supplied password."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return "Le mot de passe doit contenir entre 12 et 128 caractères."
    if not any(character.islower() for character in password):
        return "Le mot de passe doit contenir une minuscule."
    if not any(character.isupper() for character in password):
        return "Le mot de passe doit contenir une majuscule."
    if not any(character.isdigit() for character in password):
        return "Le mot de passe doit contenir un chiffre."
    if not any(not character.isalnum() for character in password):
        return "Le mot de passe doit contenir un caractère spécial."

    common_words = set(COMMON_WORDS_PATH.read_text(encoding="utf-8").splitlines())
    comparable_password = unicodedata.normalize("NFKC", password).casefold()
    normalized_words = WORD_PATTERN.findall(comparable_password)
    if any(common_word in word for word in normalized_words for common_word in common_words):
        return "Le mot de passe contient un mot anglais trop courant."
    return None


def hash_password(password: str) -> str:
    """Hash a validated password with Argon2id and a random salt."""
    return HASHER.hash(password)


def verify_password(password_hash: str, candidate: str) -> bool:
    """Verify credentials while returning the same result for malformed hashes."""
    try:
        return HASHER.verify(password_hash, candidate)
    except (VerificationError, InvalidHashError):
        return False
