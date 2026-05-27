"""Behavior tests for the progressive asynchronous lessons."""

import asyncio
import unittest

from lessons.lesson_cancellation import cancel_after_first_completion
from lessons.lesson_retry import FlakyPageFetcher, fetch_with_retry
from lessons.lesson_semaphore import measure_limited_concurrency
from lessons.lesson_timeout import fetch_with_timeout
from shared import HOME_URL


class ProgressiveLessonTests(unittest.TestCase):
    """Verify the runnable examples demonstrate their promised behaviors."""

    def test_timeout_returns_none_after_the_budget_expires(self) -> None:
        result = asyncio.run(fetch_with_timeout(HOME_URL, timeout_seconds=0.001))
        self.assertIsNone(result)

    def test_retry_recovers_from_temporary_failures(self) -> None:
        fetcher = FlakyPageFetcher(failures_before_success=2)
        result = asyncio.run(
            fetch_with_retry(
                fetcher.fetch,
                HOME_URL,
                max_attempts=3,
                base_delay_seconds=0,
            )
        )
        self.assertIn("Fetched", result)
        self.assertEqual(fetcher.attempts, 3)

    def test_semaphore_limits_active_requests(self) -> None:
        maximum_active_requests = asyncio.run(
            measure_limited_concurrency(
                [f"https://learn.example.com/{number}" for number in range(5)],
                limit=2,
            )
        )
        self.assertEqual(maximum_active_requests, 2)

    def test_invalid_retry_and_semaphore_limits_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            asyncio.run(
                fetch_with_retry(
                    FlakyPageFetcher(0).fetch,
                    HOME_URL,
                    max_attempts=0,
                )
            )
        with self.assertRaises(ValueError):
            asyncio.run(measure_limited_concurrency([HOME_URL], limit=0))

    def test_cancellation_collects_slow_tasks(self) -> None:
        completed, cancelled = asyncio.run(
            cancel_after_first_completion({"fast": 0, "slow": 0.05})
        )
        self.assertEqual(completed, {"fast"})
        self.assertEqual(cancelled, {"slow"})

    def test_cancellation_handles_no_requests(self) -> None:
        completed, cancelled = asyncio.run(cancel_after_first_completion({}))
        self.assertEqual(completed, set())
        self.assertEqual(cancelled, set())


if __name__ == "__main__":
    unittest.main()
