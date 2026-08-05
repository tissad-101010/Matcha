"""Command-line entry point for deterministic demonstration data."""

from app.config import build_config
from app.seed.demo import PROFILE_COUNT, seed_database


def main() -> int:
    """Create the demo population and print a concise result."""
    config = build_config()
    result = seed_database(str(config["DATABASE_URL"]), config)
    if result == "already_seeded":
        print(f"Seed déjà présent : {PROFILE_COUNT} profils, aucune duplication.")
    else:
        print(f"Seed créé : {PROFILE_COUNT} profils fictifs et avatars privés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
