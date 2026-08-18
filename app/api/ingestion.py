from fastapi import APIRouter

from app.database import SessionLocal
from app.ingestion.engine import IngestionEngine
from app.sources.public_source import PublicJobSource
from app.sources.remoteok_source import RemoteOKJobSource


router = APIRouter()


@router.post("/ingest")
def trigger_ingestion():

    engine = IngestionEngine(
        sources=[
            PublicJobSource(),
            RemoteOKJobSource(),
        ]
    )

    db = SessionLocal()

    try:
        run = engine.run(db)

        return {
            "run_id": run.id,
            "source": run.source,
            "status": run.status,
            "fetched": run.records_fetched,
            "inserted": run.records_inserted,
            "skipped": run.records_skipped,
            "error": run.error,
        }

    finally:
        db.close()