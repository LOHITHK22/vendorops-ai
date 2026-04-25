import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.observability.logging import get_logger, log_event

T = TypeVar("T")
logger = get_logger(__name__)


class RetryExhaustedError(Exception):
    def __init__(self, attempts: int, cause: Exception) -> None:
        super().__init__(f"Operation failed after {attempts} attempts: {cause}")
        self.attempts = attempts
        self.cause = cause


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay_seconds: float,
    retryable_exceptions: tuple[type[Exception], ...],
    operation_name: str,
    on_retry: Callable[[int, Exception, float], Awaitable[None]] | None = None,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except retryable_exceptions as exc:
            last_error = exc
            if attempt >= attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            log_event(
                logger,
                logging.WARNING,
                "retry.scheduled",
                "Retry scheduled",
                operation=operation_name,
                attempt=attempt,
                next_attempt=attempt + 1,
                delay_seconds=delay,
                error_type=type(exc).__name__,
            )
            if on_retry:
                await on_retry(attempt, exc, delay)
            if delay > 0:
                await asyncio.sleep(delay)

    if last_error is None:
        last_error = RuntimeError("retry_async was called with no attempts")
    raise RetryExhaustedError(attempts, last_error) from last_error
