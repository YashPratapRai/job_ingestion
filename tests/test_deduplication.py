from app.ingestion.normalizer import get_job_key
from app.models.job import Job


def test_same_job_generates_same_key():

    job1 = Job(
        external_id="job-123",
        title="Software Engineer",
        company="Acme",
        location="Remote",
        description="Build software.",
        url="https://example.com/jobs/123",
        source="himalayas",
    )

    job2 = Job(
        external_id="job-123",
        title="Software Engineer",
        company="Acme",
        location="Remote",
        description="Build software.",
        url="https://example.com/jobs/123",
        source="himalayas",
    )

    assert get_job_key(job1) == get_job_key(job2)


def test_different_jobs_generate_different_keys():

    job1 = Job(
        external_id="job-123",
        title="Software Engineer",
        company="Acme",
        location="Remote",
        description="Build software.",
        url="https://example.com/jobs/123",
        source="himalayas",
    )

    job2 = Job(
        external_id="job-456",
        title="Data Scientist",
        company="Acme",
        location="Remote",
        description="Analyze data.",
        url="https://example.com/jobs/456",
        source="himalayas",
    )

    assert get_job_key(job1) != get_job_key(job2)