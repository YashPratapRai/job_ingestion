import httpx

from app.config import settings
from app.sources.base import JobSource


class RemoteOKJobSource(JobSource):

    @property
    def name(self) -> str:
        return "remoteok"

    def __init__(self, url: str | None = None):
        self.url = url or settings.remoteok_source_url

    def fetch(self) -> list[dict]:
        self.rate_limiter.wait()
        
        response = httpx.get(
            self.url,
            timeout=settings.request_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "JobIngestionDemo/1.0"
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise ValueError(
                "Remote OK returned an unexpected response"
            )

        jobs = []

        for item in data:

            if not isinstance(item, dict):
                continue

            # Remote OK includes metadata in the response.
            # Actual job records contain a position and URL.
            title = item.get("position")
            url = item.get("url")

            if not title or not url:
                continue

            jobs.append({
                "external_id": str(
                    item.get("id") or url
                ),

                "title": title,

                "description": (
                    item.get("description") or ""
                ),

                "url": url,

                "published_at": item.get(
                    "date"
                ),

                "company": item.get(
                    "company"
                ),

                "location": item.get(
                    "location"
                ),

                "source": "remoteok",
            })

        return jobs