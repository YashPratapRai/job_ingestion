from app.ingestion.validator import validate_job


def test_valid_job_passes_validation():

    job = {
        "external_id": "job-123",
        "title": "Python Developer",
        "url": "https://example.com/job-123",
        "source": "test-source",
        "company": "Example",
        "location": "Remote",
    }

    valid, errors = validate_job(job)

    assert valid is True
    assert errors == []


def test_missing_required_field_fails_validation():

    job = {
        "title": "Python Developer",
        "url": "https://example.com/job-123",
        "source": "test-source",
    }

    valid, errors = validate_job(job)

    assert valid is False
    assert "Missing required field: external_id" in errors


def test_invalid_field_type_fails_validation():

    job = {
        "external_id": "job-123",
        "title": 123,
        "url": "https://example.com/job-123",
        "source": "test-source",
    }

    valid, errors = validate_job(job)

    assert valid is False
    assert "title must be a string" in errors