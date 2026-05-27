"""Lesson: limit active asynchronous requests with a semaphore."""

import asyncio


class RequestCounter:
    """Record current and maximum simultaneous simulated requests."""

    def __init__(self) -> None:
        self.active_requests = 0
        self.maximum_active_requests = 0

    async def fetch(self, url: str, semaphore: asyncio.Semaphore) -> str:
        """Fetch one simulated page only after acquiring a concurrency slot."""
        async with semaphore:
            self.active_requests += 1
            self.maximum_active_requests = max(
                self.maximum_active_requests,
                self.active_requests,
            )
            try:
                await asyncio.sleep(0.02)
                return url
            finally:
                self.active_requests -= 1


async def measure_limited_concurrency(urls: list[str], limit: int) -> int:
    """Fetch every URL and return the highest observed active request count."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    semaphore = asyncio.Semaphore(limit)
    counter = RequestCounter()
    await asyncio.gather(*(counter.fetch(url, semaphore) for url in urls))
    return counter.maximum_active_requests


async def main() -> None:
    """Show that many scheduled tasks can obey a smaller active limit."""
    urls = [f"https://learn.example.com/page/{number}" for number in range(6)]
    observed_maximum = await measure_limited_concurrency(urls, limit=2)
    print("Tasks scheduled:", len(urls))
    print("Maximum active requests:", observed_maximum)


if __name__ == "__main__":
    asyncio.run(main())
