from app.ingestion.circuit_breaker import CircuitBreaker


def test_circuit_opens_after_failure_threshold():

    breaker = CircuitBreaker(
        failure_threshold=3,
        cooldown_seconds=60,
    )

    source = "himalayas"

    assert breaker.allow_request(source) is True

    breaker.record_failure(source)

    assert breaker.failure_count(source) == 1
    assert breaker.allow_request(source) is True

    breaker.record_failure(source)

    assert breaker.failure_count(source) == 2
    assert breaker.allow_request(source) is True

    breaker.record_failure(source)

    assert breaker.failure_count(source) == 3

    assert breaker.allow_request(source) is False
    assert breaker.is_open(source) is True


def test_success_resets_failure_count():

    breaker = CircuitBreaker(
        failure_threshold=3,
        cooldown_seconds=60,
    )

    source = "himalayas"

    breaker.record_failure(source)
    breaker.record_failure(source)

    assert breaker.failure_count(source) == 2

    breaker.record_success(source)

    assert breaker.failure_count(source) == 0
    assert breaker.allow_request(source) is True


def test_different_sources_have_independent_state():

    breaker = CircuitBreaker(
        failure_threshold=2,
        cooldown_seconds=60,
    )

    breaker.record_failure("himalayas")
    breaker.record_failure("himalayas")

    assert breaker.allow_request("himalayas") is False

    assert breaker.allow_request("remoteok") is True