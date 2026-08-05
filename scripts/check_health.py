"""Wait briefly for the public application readiness endpoint."""

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

MAX_ATTEMPTS = 30


def app_port() -> str:
    """Read APP_PORT from the private environment file."""
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("APP_PORT="):
            return line.partition("=")[2]
    raise RuntimeError("APP_PORT est absent du fichier .env")


def main() -> int:
    """Return success when Nginx and every backend dependency are ready."""
    url = f"http://127.0.0.1:{app_port()}/health/ready"
    for _attempt in range(MAX_ATTEMPTS):
        try:
            with urlopen(url, timeout=3) as response:
                payload = json.load(response)
                print(json.dumps(payload, ensure_ascii=False))
                return 0
        except (HTTPError, URLError, TimeoutError):
            time.sleep(2)
    print(f"Application indisponible après {MAX_ATTEMPTS * 2} secondes : {url}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
