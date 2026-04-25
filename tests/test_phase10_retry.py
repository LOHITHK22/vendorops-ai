import pytest

from app.observability.retry import RetryExhaustedError, retry_async


class TransientFailure(Exception):
    pass


@pytest.mark.asyncio
async def test_retry_async_recovers_from_transient_failure() -> None:
    attempts = 0
    retry_events: list[tuple[int, str, float]] = []

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TransientFailure("temporary upstream failure")
        return "success"

    async def on_retry(attempt: int, exc: Exception, delay: float) -> None:
        retry_events.append((attempt, type(exc).__name__, delay))

    result = await retry_async(
        operation,
        attempts=3,
        base_delay_seconds=0,
        retryable_exceptions=(TransientFailure,),
        operation_name="test_operation",
        on_retry=on_retry,
    )

    assert result == "success"
    assert attempts == 3
    assert retry_events == [
        (1, "TransientFailure", 0),
        (2, "TransientFailure", 0),
    ]


@pytest.mark.asyncio
async def test_retry_async_raises_after_attempts_are_exhausted() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise TransientFailure("still down")

    with pytest.raises(RetryExhaustedError) as exc_info:
        await retry_async(
            operation,
            attempts=2,
            base_delay_seconds=0,
            retryable_exceptions=(TransientFailure,),
            operation_name="test_operation",
        )

    assert attempts == 2
    assert exc_info.value.attempts == 2
    assert isinstance(exc_info.value.cause, TransientFailure)
