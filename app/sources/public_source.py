import feedparser
import httpx

from bs4 import BeautifulSoup

from app.config import settings
from app.sources.base import JobSource
from app.ingestion.retry import run_with_retry
from app.ingestion.rate_limiter import RateLimiter


class PublicJobSource(JobSource):
    @property
    def name(self) -> str:
        return "himalayas"

    def __init__(self, url: str | None = None):
        self.url = url or settings.source_url
        self.rate_limiter = RateLimiter(
            settings.request_interval
        )

    def fetch(self) -> list[dict]:

        def request():
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

            return response

        response = run_with_retry(request)

        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:
            raise ValueError("Invalid or unreadable feed")

        jobs = []

        for entry in feed.entries:
            company = self._extract_company(entry)

            description = self._extract_description(entry)

            jobs.append({
                "external_id": entry.get("id") or entry.get("guid"),
                "title": entry.get("title"),
                "description": description,
                "url": entry.get("link"),
                "published_at": entry.get("published"),
                "company": company,
                "location": entry.get(
                    "himalayasjobs_locationrestriction"
                ),
                "source": "himalayas",
            })

        return jobs

    @staticmethod
    def _extract_company(entry) -> str | None:
        """
        Extract company name from the source.

        The source-provided company field is currently unreliable,
        so we fall back to the company link inside the job content.
        """

        company = entry.get("himalayasjobs_companyname")

        if company and company.strip().lower() != "name":
            return company.strip()

    # Prefer full HTML content because the company link
    # is available there.
        content = entry.get("content")

        if content:
            html = content[0].get("value", "")
        else:
            html = entry.get("summary", "")

        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if "/companies/" in href:
                company_name = link.get_text(strip=True)

                if company_name:
                    return company_name

        return None
        

    @staticmethod
    def _extract_description(entry) -> str:
        """
        Convert the HTML job description into clean text.
        """

        content = entry.get("content")

        if content:
            html = content[0].get("value", "")

        else:
            html = entry.get("summary", "")

        soup = BeautifulSoup(html, "html.parser")

        return soup.get_text(
            separator=" ",
            strip=True
        )