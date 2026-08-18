import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from app.config import settings


T = TypeVar("T")


RETRYABLE_STATUS_CODES = {
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
}


def run_with_retry(
    operation: Callable[[], T],
) -> T:
    """
    Execute an operation with exponential backoff.

    Retries are performed for:
    - HTTP 429
    - HTTP 5xx
    - connection errors
    - timeouts

    Non-retryable HTTP errors are raised immediately.
    """

    last_exception = None

    for attempt in range(settings.max_retries + 1):

        try:
            return operation()

        except httpx.HTTPStatusError as exc:

            status_code = exc.response.status_code

            if status_code not in RETRYABLE_STATUS_CODES:
                raise

            last_exception = exc

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
            ConnectionError,
        ) as exc:

            last_exception = exc

        if attempt >= settings.max_retries:
            break

        delay = settings.base_backoff * (2 ** attempt)

        print(
            f"Retrying in {delay:.1f}s "
            f"(attempt {attempt + 1}/{settings.max_retries})"
        )

        time.sleep(delay)

    raise RuntimeError(
        "Operation failed after maximum retries"
    ) from last_exception