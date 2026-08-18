import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Job Ingestion Service"

    source_url: str = os.getenv(
        "SOURCE_URL",
        "https://himalayas.app/jobs/rss"
    )

    remoteok_source_url: str = os.getenv(
        "REMOTEOK_SOURCE_URL",
        "https://remoteok.com/api"
    )

    request_timeout: float = 20.0

    max_retries: int = 3

    base_backoff: float = 1.0

    request_interval: float = 2.0


settings = Settings()