"""Run all crawler implementations against the same offline website."""

import asyncio
from collections.abc import Callable
from time import perf_counter

from async_crawler import AsyncWebCrawler
from shared import HOME_URL
from synchronous_crawlers import SequentialWebCrawler, ThreadPoolWebCrawler


def measure_run(label: str, crawler_run: Callable[[], list[str]]) -> None:
    """Run a blocking crawler and print its elapsed time and discovered pages."""
    started_at = perf_counter()
    pages = crawler_run()
    elapsed_seconds = perf_counter() - started_at
    print(f"{label:<12} {elapsed_seconds:.3f}s  {len(pages)} pages")


async def measure_async_run() -> None:
    """Run the async crawler and print its elapsed time and discovered pages."""
    started_at = perf_counter()
    pages = await AsyncWebCrawler(HOME_URL, max_concurrency=2).run()
    elapsed_seconds = perf_counter() - started_at
    print(f"{'Asyncio':<12} {elapsed_seconds:.3f}s  {len(pages)} pages")


async def main() -> None:
    """Compare the crawler styles under the same simulated network delays."""
    print("Crawler       Time    Result")
    print("----------------------------")
    measure_run("Sequential", lambda: SequentialWebCrawler(HOME_URL).run())
    measure_run(
        "Thread pool",
        lambda: ThreadPoolWebCrawler(HOME_URL, max_workers=2).run(),
    )
    await measure_async_run()


if __name__ == "__main__":
    asyncio.run(main())
