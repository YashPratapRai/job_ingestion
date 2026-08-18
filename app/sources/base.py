from abc import ABC, abstractmethod
from typing import Any


class JobSource(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique source name."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """Fetch raw jobs from the source."""
        raise NotImplementedError