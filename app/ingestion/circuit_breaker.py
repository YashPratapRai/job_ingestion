from dataclasses import dataclass
from datetime import datetime, UTC, timedelta


@dataclass
class CircuitState:
    failure_count: int = 0
    opened_at: datetime | None = None


class CircuitBreaker:

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: int = 1800,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._states: dict[str, CircuitState] = {}

    def _get_state(self, source_name: str) -> CircuitState:
        if source_name not in self._states:
            self._states[source_name] = CircuitState()

        return self._states[source_name]

    def allow_request(self, source_name: str) -> bool:
        state = self._get_state(source_name)

        # Circuit is closed.
        if state.opened_at is None:
            return True

        now = datetime.now(UTC)

        cooldown_ends = (
            state.opened_at
            + timedelta(seconds=self.cooldown_seconds)
        )

        # Cooldown is still active.
        if now < cooldown_ends:
            return False

        # Cooldown expired: allow one health probe.
        return True

    def record_success(self, source_name: str) -> None:
        self._states[source_name] = CircuitState()

    def record_failure(self, source_name: str) -> None:
        state = self._get_state(source_name)

        state.failure_count += 1

        if state.failure_count >= self.failure_threshold:
            state.opened_at = datetime.now(UTC)

    def failure_count(self, source_name: str) -> int:
        return self._get_state(source_name).failure_count

    def is_open(self, source_name: str) -> bool:
        state = self._get_state(source_name)

        if state.opened_at is None:
            return False

        return not self.allow_request(source_name)