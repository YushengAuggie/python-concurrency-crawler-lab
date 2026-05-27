"""Lesson: retry temporary failures with bounded exponential backoff."""

import asyncio
from collections.abc import Awaitable, Callable


class TemporaryFetchError(ConnectionError):
    """Represent a request failure that may succeed when tried again."""


class FlakyPageFetcher:
    """Fail a configured number of times before returning page HTML."""

    def __init__(self, failures_before_success: int):
        self.failures_remaining = failures_before_success
        self.attempts = 0

    async def fetch(self, url: str) -> str:
        """Fetch one page after simulating temporary failures."""
        self.attempts += 1
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise TemporaryFetchError(f"Temporary failure for {url}")
        return f"<html>Fetched {url}</html>"


async def fetch_with_retry(
    fetch: Callable[[str], Awaitable[str]],
    url: str,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.01,
) -> str:
    """Retry temporary failures with a short exponentially increasing delay."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    for attempt_number in range(1, max_attempts + 1):
        try:
            return await fetch(url)
        except TemporaryFetchError:
            if attempt_number == max_attempts:
                raise

            delay_seconds = base_delay_seconds * (2 ** (attempt_number - 1))
            await asyncio.sleep(delay_seconds)

async def main() -> None:
    """Show a temporary failure recovering within the retry budget."""
    fetcher = FlakyPageFetcher(failures_before_success=2)
    html_content = await fetch_with_retry(fetcher.fetch, "https://learn.example.com/")

    print("Request succeeded:", "Fetched" in html_content)
    print("Attempts used:", fetcher.attempts)


if __name__ == "__main__":
    asyncio.run(main())
