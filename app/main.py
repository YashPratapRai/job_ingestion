from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine

from app.models.job import Job
from app.models.ingestion_run import IngestionRun

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.ingestion import router as ingestion_router
from app.api.runs import router as runs_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Job Ingestion Service",
    description=(
        "Resilient multi-source job ingestion pipeline "
        "using permitted public feeds."
    ),
    version="1.0.0",
)


# Serve static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


# Home page
@app.get("/")
def root():
    return FileResponse("static/index.html")


# API routes
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(ingestion_router)
app.include_router(runs_router)