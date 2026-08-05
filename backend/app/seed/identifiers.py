"""Stable identifiers shared by relational fixtures and object storage."""

from uuid import NAMESPACE_URL, UUID, uuid5

SEED_NAMESPACE = uuid5(NAMESPACE_URL, "matcha.demo.seed.v1")


def stable_id(kind: str, value: int | str) -> UUID:
    """Build stable identifiers so reruns address the same rows and objects."""
    return uuid5(SEED_NAMESPACE, f"{kind}:{value}")
