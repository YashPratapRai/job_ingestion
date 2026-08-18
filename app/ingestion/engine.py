from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.normalizer import (
    get_job_key,
    normalize_job,
)
from app.ingestion.validator import validate_job
from app.ingestion.quarantine import quarantine_job
from app.ingestion.circuit_breaker import CircuitBreaker

from app.models.ingestion_run import IngestionRun
from app.models.job import Job


class IngestionEngine:

    def __init__(
        self,
        sources: list,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        if not sources:
            raise ValueError("At least one source is required")

        self.sources = sources

        # Keep one circuit breaker instance for this engine.
        # If one is supplied, use it; otherwise create a default one.
        self.circuit_breaker = (
            circuit_breaker
            or CircuitBreaker(
                failure_threshold=3,
                cooldown_seconds=1800,
            )
        )

    def run(self, session: Session) -> IngestionRun:

        # ---------------------------------------------------------
        # Create ingestion run
        # ---------------------------------------------------------

        run = IngestionRun(
            source="multi-source",
            started_at=datetime.now(UTC),
            status="RUNNING",
        )

        session.add(run)
        session.commit()
        session.refresh(run)

        selected_source = None
        primary_error = None
        raw_jobs = None

        skipped_sources = []

        # ---------------------------------------------------------
        # Try sources in priority order
        # ---------------------------------------------------------

        for source in self.sources:

            # -----------------------------------------------------
            # Circuit breaker check
            # -----------------------------------------------------

            if not self.circuit_breaker.allow_request(
                source.name
            ):
                print(
                    f"Skipping source {source.name}: "
                    f"circuit breaker is OPEN"
                )

                skipped_sources.append(source.name)

                continue

            try:

                print(
                    f"Trying source: {source.name}"
                )

                candidate_jobs = source.fetch()

                # -------------------------------------------------
                # Empty response
                # -------------------------------------------------

                if not candidate_jobs:

                    print(
                        f"Source {source.name} "
                        f"returned zero jobs"
                    )

                    # Empty response is not automatically a failure.
                    # Do not increment the circuit breaker.
                    continue

                # -------------------------------------------------
                # Successful fetch
                # -------------------------------------------------

                self.circuit_breaker.record_success(
                    source.name
                )

                raw_jobs = candidate_jobs
                selected_source = source.name

                print(
                    f"Using source: {source.name}"
                )

                break

            except Exception as exc:

                print(
                    f"Source {source.name} failed: {exc}"
                )

                # ---------------------------------------------
                # Record failure in circuit breaker
                # ---------------------------------------------

                self.circuit_breaker.record_failure(
                    source.name
                )

                print(
                    f"{source.name} failure count: "
                    f"{self.circuit_breaker.failure_count(source.name)}"
                )

                # ---------------------------------------------
                # Preserve first error for run status
                # ---------------------------------------------

                if primary_error is None:
                    primary_error = str(exc)

        # ---------------------------------------------------------
        # No source produced usable data
        # ---------------------------------------------------------

        if not raw_jobs:

            run.status = "DEGRADED"

            if primary_error:

                run.error = (
                    f"All usable sources failed. "
                    f"First error: {primary_error}"
                )

            elif skipped_sources:

                run.error = (
                    "No usable source available. "
                    f"Skipped due to open circuit: "
                    f"{', '.join(skipped_sources)}"
                )

            else:

                run.error = (
                    "All sources returned zero jobs."
                )

            run.completed_at = datetime.now(UTC)

            session.commit()

            return run

        # ---------------------------------------------------------
        # Process selected source
        # ---------------------------------------------------------

        try:

            run.source = selected_source
            run.records_fetched = len(raw_jobs)

            inserted = 0
            skipped = 0
            quarantined = 0

            # -----------------------------------------------------
            # Process every raw job
            # -----------------------------------------------------

            for raw_job in raw_jobs:

                try:

                    # ---------------------------------------------
                    # Normalize
                    # ---------------------------------------------

                    job = normalize_job(raw_job)

                    # ---------------------------------------------
                    # Validate
                    # ---------------------------------------------

                    valid, errors = validate_job(job)

                    if not valid:

                        print(
                            f"Quarantining invalid job: "
                            f"{errors}"
                        )

                        quarantine_job(
                            job=raw_job,
                            errors=errors,
                            source=selected_source,
                        )

                        quarantined += 1

                        continue

                    # ---------------------------------------------
                    # Generate deterministic job key
                    # ---------------------------------------------

                    job_key = get_job_key(job)

                    # ---------------------------------------------
                    # Deduplication
                    # ---------------------------------------------

                    existing = session.scalar(
                        select(Job).where(
                            Job.job_key == job_key
                        )
                    )

                    if existing:

                        skipped += 1

                        continue

                    # ---------------------------------------------
                    # Insert new job
                    # ---------------------------------------------

                    db_job = Job(
                        job_key=job_key,
                        external_id=job.external_id,
                        title=job.title,
                        company=job.company,
                        location=job.location,
                        description=job.description,
                        url=str(job.url),
                        published_at=job.published_at,
                        source=job.source,
                    )

                    session.add(db_job)

                    inserted += 1

                except Exception as exc:

                    # ---------------------------------------------
                    # Unexpected malformed record
                    # ---------------------------------------------

                    print(
                        f"Quarantining malformed job: "
                        f"{exc}"
                    )

                    quarantine_job(
                        job=raw_job,
                        errors=[str(exc)],
                        source=selected_source,
                    )

                    quarantined += 1

            # -----------------------------------------------------
            # Commit inserted jobs
            # -----------------------------------------------------

            session.commit()

            run.records_inserted = inserted
            run.records_skipped = skipped

            # -----------------------------------------------------
            # Determine final ingestion status
            # -----------------------------------------------------

            if quarantined > 0:

                run.status = "DEGRADED"

                messages = []

                if primary_error:

                    messages.append(
                        f"Primary source failed: "
                        f"{primary_error}"
                    )

                messages.append(
                    f"{quarantined} invalid records "
                    f"were quarantined."
                )

                run.error = " ".join(messages)

            elif primary_error:

                # Primary source failed but fallback worked.
                run.status = "SUCCESS_FALLBACK"

                run.error = (
                    f"Primary source failed: "
                    f"{primary_error}"
                )

            else:

                run.status = "SUCCESS"

            # -----------------------------------------------------
            # Finish run
            # -----------------------------------------------------

            run.completed_at = datetime.now(UTC)

            session.commit()

            return run

        except Exception as exc:

            # -----------------------------------------------------
            # Unexpected pipeline-level failure
            # -----------------------------------------------------

            session.rollback()

            run.status = "FAILED"
            run.error = str(exc)
            run.completed_at = datetime.now(UTC)

            session.add(run)
            session.commit()

            return run