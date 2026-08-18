import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


QUARANTINE_DIR = Path("quarantine")


def quarantine_job(
    job: Any,
    errors: list[str],
    source: str,
) -> None:

    QUARANTINE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    filename = (
        f"{source}_{timestamp}.json"
    )

    payload = {
        "source": source,
        "quarantined_at": datetime.now(UTC).isoformat(),
        "errors": errors,
        "job": job,
    }

    path = QUARANTINE_DIR / filename

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
            default=str,
        )