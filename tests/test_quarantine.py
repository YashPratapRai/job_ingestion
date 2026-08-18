import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.engine import IngestionEngine
from app.models.job import Job
from app.sources.base import JobSource


class InvalidSource(JobSource):

    @property
    def name(self) -> str:
        return "test-invalid"

    def fetch(self):
        return [
            {
                "external_id": "invalid-001",
                "title": "",
                "description": "Invalid test job",
                "url": "https://example.com/invalid",
                "published_at": None,
                "company": "Test Company",
                "location": "Remote",
                "source": "test-invalid",
            }
        ]


def test_invalid_job_is_quarantined(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

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
            sources=[InvalidSource()]
        )

        run = ingestion_engine.run(session)

        # Invalid record should make the run degraded.
        assert run.status == "DEGRADED"

        # One record was fetched.
        assert run.records_fetched == 1

        # Invalid record must NOT enter the jobs table.
        assert run.records_inserted == 0

        jobs = session.scalars(
            select(Job)
        ).all()

        assert len(jobs) == 0

        # Quarantine file should exist.
        quarantine_dir = tmp_path / "quarantine"

        files = list(
            quarantine_dir.glob("*.json")
        )

        assert len(files) == 1

        # Inspect quarantine contents.
        with files[0].open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        assert data["source"] == "test-invalid"

        assert (
            data["job"]["external_id"]
            == "invalid-001"
        )

        assert len(data["errors"]) > 0

    finally:

        session.close()
        engine.dispose()