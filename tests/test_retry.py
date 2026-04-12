from __future__ import annotations

import unittest

from oracle.infrastructure.retry import with_retry


class RetryTest(unittest.TestCase):
    def test_should_retry_until_success_when_transient_error_occurs(self) -> None:
        attempts = {"count": 0}

        def flaky_operation() -> str:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("temporary")
            return "ok"

        result = with_retry(flaky_operation, max_retries=3, delay_seconds=0.0)

        self.assertEqual(result, "ok")
        self.assertEqual(attempts["count"], 3)


if __name__ == "__main__":
    unittest.main()
