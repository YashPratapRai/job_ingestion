from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.engine import IngestionEngine
from app.sources.base import JobSource


class FailingSource(JobSource):

    @property
    def name(self) -> str:
        return "failing-primary"

    def fetch(self):
        raise RuntimeError("Simulated primary source failure")


class FakeFallbackSource(JobSource):

    @property
    def name(self) -> str:
        return "test-fallback"

    def fetch(self):
        return [
            {
                "external_id": "fallback-test-001",
                "title": "Fallback Engineer",
                "description": "Test fallback job",
                "url": "https://example.com/jobs/fallback-test-001",
                "published_at": "Tue, 18 Aug 2026 05:45:35 GMT",
                "company": "Test Company",
                "location": "Remote",
                "source": "test-fallback",
            }
        ]


def test_primary_failure_uses_fallback():

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = SessionLocal()

    try:
        ingestion_engine = IngestionEngine(
            sources=[
                FailingSource(),
                FakeFallbackSource(),
            ]
        )

        run = ingestion_engine.run(session)

        assert run.status == "SUCCESS_FALLBACK"
        assert run.source == "test-fallback"
        assert run.records_fetched == 1
        assert run.records_inserted == 1
        assert run.records_skipped == 0
        assert "Simulated primary source failure" in run.error

    finally:
        session.close()
        engine.dispose()