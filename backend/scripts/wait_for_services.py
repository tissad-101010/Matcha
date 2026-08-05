"""Wait for mandatory services before Gunicorn starts."""

import logging
import time

from app.config import build_config
from app.infrastructure import check_dependencies

LOGGER = logging.getLogger("matcha.startup")
MAX_ATTEMPTS = 60


def main() -> int:
    """Return success only when every dependency is ready."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = build_config()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        checks = check_dependencies(config)
        if all(checks.values()):
            LOGGER.info("Mandatory services are ready")
            return 0
        LOGGER.info("Waiting for services (%s/%s): %s", attempt, MAX_ATTEMPTS, checks)
        time.sleep(2)

    LOGGER.error("Mandatory services did not become ready")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
