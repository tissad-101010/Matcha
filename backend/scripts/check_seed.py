"""Validate the mandatory demonstration dataset."""

import psycopg

from app.config import build_config
from app.seed.demo import PROFILE_COUNT
from app.seed.storage import s3_client


def main() -> int:
    """Check relational counts, complete public profiles and private avatar objects."""
    config = build_config()
    with psycopg.connect(str(config["DATABASE_URL"])) as connection:
        counts = connection.execute(
            """
            SELECT
                (SELECT count(*) FROM accounts),
                (SELECT count(*) FROM profiles),
                (SELECT count(*) FROM photos),
                (SELECT count(*) FROM public_profiles),
                (SELECT count(*) FROM current_consents WHERE purpose = 'matching_preferences'),
                (SELECT count(*) FROM current_consents WHERE purpose = 'gps_location'),
                (SELECT count(*) FROM user_locations WHERE source = 'gps_reduced')
            """
        ).fetchone()
    expected = (PROFILE_COUNT,) * 5 + (PROFILE_COUNT // 4, PROFILE_COUNT // 4)
    if counts != expected:
        raise RuntimeError(f"Seed relationnel incomplet : {counts}, attendu : {expected}")

    response = s3_client(config).list_objects_v2(Bucket="profile-photos", MaxKeys=1000)
    object_count = int(response.get("KeyCount", 0))
    if object_count != PROFILE_COUNT:
        raise RuntimeError(f"Avatars incomplets : {object_count}, attendu : {PROFILE_COUNT}")

    print(f"Seed validé : {PROFILE_COUNT} profils complets et {object_count} avatars privés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
