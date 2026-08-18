import hashlib
import re
from datetime import datetime

from app.models.schemas import JobSchema


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%a, %d %b %Y %H:%M:%S %Z"
        )
    except ValueError:
        return None


def normalize_job(raw_job: dict) -> JobSchema:
    return JobSchema(
        external_id=clean_text(
            raw_job.get("external_id")
        ),

        title=clean_text(
            raw_job.get("title")
        ),

        company=clean_text(
            raw_job.get("company")
        ) or None,

        location=clean_text(
            raw_job.get("location")
        ) or None,

        description=clean_text(
            raw_job.get("description")
        ),

        url=raw_job.get("url"),

        published_at=parse_datetime(
            raw_job.get("published_at")
        ),

        source=clean_text(
            raw_job.get("source")
        ),
    )


def get_job_key(job: JobSchema) -> str:
    value = f"{job.source}:{job.external_id}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()