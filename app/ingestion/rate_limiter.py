import time
from threading import Lock


class RateLimiter:
    """
    Simple process-local rate limiter.

    Ensures that requests are separated by at least
    `min_interval` seconds.
    """

    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self._last_request_time = 0.0
        self._lock = Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()

            elapsed = now - self._last_request_time

            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

            self._last_request_time = time.monotonic()