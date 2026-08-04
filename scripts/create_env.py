"""Create a private local environment file without overwriting it."""

from pathlib import Path
from secrets import token_urlsafe

EXAMPLE_PATH = Path(".env.example")
ENV_PATH = Path(".env")


def main() -> None:
    """Copy the example while replacing local placeholder secrets."""
    if ENV_PATH.exists():
        print("Configuration .env déjà présente, elle reste inchangée.")
        return

    content = EXAMPLE_PATH.read_text(encoding="utf-8")
    replacements = {
        "change-me-with-at-least-32-random-characters": f"matcha-{token_urlsafe(48)}",
        "change-me-postgres-password": f"matcha-{token_urlsafe(32)}",
        "change-me-valkey-password": f"matcha-{token_urlsafe(32)}",
        "change-me-minio-password": f"matcha-{token_urlsafe(32)}",
    }
    for placeholder, secret in replacements.items():
        content = content.replace(placeholder, secret)

    ENV_PATH.write_text(content, encoding="utf-8")
    ENV_PATH.chmod(0o600)
    print("Configuration locale créée dans .env (permissions 0600).")


if __name__ == "__main__":
    main()
