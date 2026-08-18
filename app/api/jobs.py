from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job
from sqlalchemy import select, func

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/jobs")
def get_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 100)

    total = db.scalar(
        select(func.count()).select_from(Job)
    )

    jobs = db.scalars(
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
    ).all()

    return {
        "count": total,
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "source": job.source,
                "published_at": job.published_at,
            }
            for job in jobs
        ],
    }