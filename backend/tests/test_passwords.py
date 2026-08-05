"""Password policy and hashing tests."""

from app.auth.passwords import hash_password, password_error, verify_password


def test_strong_password_is_hashed_with_argon2id() -> None:
    password = "Rivière-7-Nuages!"
    password_hash = hash_password(password)

    assert password_error(password) is None
    assert password_hash.startswith("$argon2id$")
    assert password not in password_hash
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "incorrect")


def test_common_english_word_is_rejected() -> None:
    assert password_error("Welcome-42-Fort!") == (
        "Le mot de passe contient un mot anglais trop courant."
    )


def test_common_word_embedded_in_a_longer_token_is_rejected() -> None:
    assert password_error("UltraPassword42!") == (
        "Le mot de passe contient un mot anglais trop courant."
    )


def test_malformed_hash_never_authenticates() -> None:
    assert not verify_password("not-a-hash", "Rivière-7-Nuages!")
