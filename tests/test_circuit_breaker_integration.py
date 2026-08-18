from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.circuit_breaker import CircuitBreaker
from app.ingestion.engine import IngestionEngine
from app.models.job import Job
from app.sources.base import JobSource


class FailingSource(JobSource):

    @property
    def name(self) -> str:
        return "failing-primary"

    def fetch(self):
        raise RuntimeError("Primary source is down")


class FallbackSource(JobSource):

    @property
    def name(self) -> str:
        return "fallback-source"

    def fetch(self):
        return [
            {
                "external_id": "integration-001",
                "title": "Fallback Engineer",
                "description": "Integration test job",
                "url": "https://example.com/jobs/integration-001",
                "published_at": None,
                "company": "Test Company",
                "location": "Remote",
                "source": "fallback-source",
            }
        ]


def test_open_circuit_skips_primary_and_uses_fallback():

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

        breaker = CircuitBreaker(
            failure_threshold=3,
            cooldown_seconds=1800,
        )

        # Simulate three previous failures.
        breaker.record_failure("failing-primary")
        breaker.record_failure("failing-primary")
        breaker.record_failure("failing-primary")

        assert breaker.allow_request(
            "failing-primary"
        ) is False

        ingestion_engine = IngestionEngine(
            sources=[
                FailingSource(),
                FallbackSource(),
            ],
            circuit_breaker=breaker,
        )

        run = ingestion_engine.run(session)

        # Primary should have been skipped.
        assert run.source == "fallback-source"

        # Because fallback succeeded.
        assert run.status == "SUCCESS"

        assert run.records_fetched == 1
        assert run.records_inserted == 1
        assert run.records_skipped == 0

        # Confirm job actually entered DB.
        jobs = session.scalars(
            select(Job)
        ).all()

        assert len(jobs) == 1
        assert jobs[0].source == "fallback-source"

    finally:

        session.close()
        engine.dispose()