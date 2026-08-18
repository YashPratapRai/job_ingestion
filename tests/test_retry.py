from app.ingestion.retry import run_with_retry


def test_retry_eventually_succeeds():
    attempts = 0

    def operation():
        nonlocal attempts

        attempts += 1

        if attempts < 3:
            raise ConnectionError("Temporary failure")

        return "success"

    result = run_with_retry(operation)

    assert result == "success"
    assert attempts == 3