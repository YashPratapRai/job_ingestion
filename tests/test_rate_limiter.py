import time

from app.ingestion.rate_limiter import RateLimiter


def test_rate_limiter_enforces_interval():

    limiter = RateLimiter(min_interval=0.2)

    limiter.wait()

    start = time.monotonic()

    limiter.wait()

    elapsed = time.monotonic() - start

    assert elapsed >= 0.18