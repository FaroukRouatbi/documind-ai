import pybreaker
import pytest
from botocore.exceptions import ClientError

from app.core.bedrock import _is_permanent, _is_transient


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "x"}}, "InvokeModel")


@pytest.mark.parametrize(
    "code",
    [
        "ThrottlingException",
        "ServiceUnavailableException",
        "ModelTimeoutException",
        "InternalServerException",
        "ModelNotReadyException",
    ],
)
def test_transient_codes_are_transient(code):
    assert _is_transient(_client_error(code)) is True
    assert _is_permanent(_client_error(code)) is False


@pytest.mark.parametrize("code", ["ValidationException", "AccessDeniedException"])
def test_permanent_codes_are_not_transient(code):
    assert _is_transient(_client_error(code)) is False
    assert _is_permanent(_client_error(code)) is True


def test_non_client_error_is_treated_as_permanent():
    assert _is_transient(ValueError("boom")) is False
    assert _is_permanent(ValueError("boom")) is True


def test_breaker_opens_after_repeated_transient_failures():
    breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, exclude=[_is_permanent])

    def always_throttle():
        raise _client_error("ThrottlingException")

    # first 2 calls pass through and count as failures
    for _ in range(2):
        with pytest.raises(ClientError):
            breaker.call(always_throttle)

    # the 3rd failure reaches fail_max and the breaker opens on that call
    with pytest.raises(pybreaker.CircuitBreakerError):
        breaker.call(always_throttle)

    # subsequent calls short-circuit without invoking the function
    with pytest.raises(pybreaker.CircuitBreakerError):
        breaker.call(always_throttle)


def test_breaker_does_not_open_on_permanent_failures():
    breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, exclude=[_is_permanent])

    def always_validation_error():
        raise _client_error("ValidationException")

    # permanent errors are excluded — they never count toward tripping
    for _ in range(10):
        with pytest.raises(ClientError):
            breaker.call(always_validation_error)
