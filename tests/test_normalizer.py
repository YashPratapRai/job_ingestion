from app.ingestion.normalizer import normalize_job


def test_normalize_job():

    raw_job = {
        "external_id": " job-123 ",
        "title": "  Software Engineer  ",
        "company": "  Acme Corp  ",
        "location": " United States ",
        "description": "Build   backend   systems.",
        "url": "https://example.com/jobs/123",
        "published_at": "Tue, 18 Aug 2026 05:45:35 GMT",
        "source": " himalayas ",
    }

    job = normalize_job(raw_job)

    assert job.external_id == "job-123"
    assert job.title == "Software Engineer"
    assert job.company == "Acme Corp"
    assert job.location == "United States"
    assert job.description == "Build backend systems."
    assert str(job.url) == "https://example.com/jobs/123"
    assert job.source == "himalayas"