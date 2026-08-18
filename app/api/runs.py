from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.jobs import get_db
from app.models.ingestion_run import IngestionRun


router = APIRouter()


@router.get("/runs")
def get_runs(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 100)

    runs = db.scalars(
        select(IngestionRun)
        .order_by(IngestionRun.id.desc())
        .limit(limit)
    ).all()

    return {
        "count": len(runs),
        "runs": [
            {
                "id": run.id,
                "source": run.source,
                "status": run.status,
                "fetched": run.records_fetched,
                "inserted": run.records_inserted,
                "skipped": run.records_skipped,
                "error": run.error,
            }
            for run in runs
        ],
    }