from typing import Any

from pydantic import HttpUrl


REQUIRED_FIELDS = {
    "external_id",
    "title",
    "url",
    "source",
}


def _to_dict(job: Any) -> dict[str, Any] | None:
    """
    Convert a normalized job object into a dictionary.
    Supports dictionaries and Pydantic-style model objects.
    """

    if isinstance(job, dict):
        return job

    # Pydantic v2
    if hasattr(job, "model_dump"):
        return job.model_dump()

    # Pydantic v1 fallback
    if hasattr(job, "dict"):
        return job.dict()

    return None


def validate_job(job: Any) -> tuple[bool, list[str]]:
    """
    Validate a normalized job.

    Returns:
        (True, []) when valid.
        (False, [errors...]) when invalid.
    """

    errors = []

    data = _to_dict(job)

    if data is None:
        return False, [
            "Job must be a dictionary or model object"
        ]

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(
                f"Missing required field: {field}"
            )

    # Title
    if "title" in data:
        if not isinstance(data["title"], str):
            errors.append(
                "title must be a string"
            )

    # URL
    if "url" in data:
        if not isinstance(
            data["url"],
            (str, HttpUrl),
        ):
            errors.append(
                "url must be a valid URL"
            )

    # Source
    if "source" in data:
        if not isinstance(
            data["source"],
            str,
        ):
            errors.append(
                "source must be a string"
            )

    # External ID
    if "external_id" in data:
        if not isinstance(
            data["external_id"],
            str,
        ):
            errors.append(
                "external_id must be a string"
            )

    return len(errors) == 0, errors