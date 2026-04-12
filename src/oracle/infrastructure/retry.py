from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retry(
    operation: Callable[[], T],
    *,
    max_retries: int,
    delay_seconds: float,
) -> T:
    attempt = 0
    while True:
        try:
            return operation()
        except Exception:
            if attempt >= max_retries:
                raise
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            attempt += 1