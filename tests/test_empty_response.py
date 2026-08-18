from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.engine import IngestionEngine
from app.sources.base import JobSource


class EmptySource(JobSource):

    @property
    def name(self) -> str:
        return "empty-source"

    def fetch(self):
        return []


def test_empty_source_does_not_delete_existing_data():

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
                EmptySource()
            ]
        )

        run = ingestion_engine.run(session)

        assert run.status == "DEGRADED"

        assert run.records_fetched == 0

        assert run.records_inserted == 0

        assert run.records_skipped == 0

        assert run.error is not None

        assert "zero jobs" in run.error

    finally:

        session.close()
        engine.dispose()