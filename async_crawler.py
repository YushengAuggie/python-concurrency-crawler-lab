"""Asyncio crawler example that coordinates non-blocking page requests."""

import asyncio
from collections import deque

from shared import HOME_URL, get_html_content_async, get_links_on_page


class AsyncWebCrawler:
    """Crawl pages concurrently with asyncio tasks on one event loop thread."""

    def __init__(self, starting_url: str, max_concurrency: int = 20):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")

        self.discovered_urls = {starting_url}
        self.urls_to_crawl = deque([starting_url])
        self.fetched_urls: list[str] = []
        self.failed_urls: set[str] = set()
        self.max_concurrency = max_concurrency

    async def fetch_links(self, url: str) -> tuple[str, list[str] | None]:
        """Fetch one page and return its URL plus links, or a failed marker."""
        try:
            html_content = await get_html_content_async(url)
        except ConnectionError:
            return url, None

        return url, get_links_on_page(html_content, url)

    async def run(self) -> list[str]:
        """Schedule bounded async tasks until no queued or running work remains."""
        pending_tasks: set[asyncio.Task[tuple[str, list[str] | None]]] = set()

        while self.urls_to_crawl or pending_tasks:
            available_task_slots = self.max_concurrency - len(pending_tasks)
            pages_to_schedule = min(
                available_task_slots, len(self.urls_to_crawl)
            )

            for _ in range(pages_to_schedule):
                url = self.urls_to_crawl.popleft()
                task = asyncio.create_task(self.fetch_links(url))
                pending_tasks.add(task)

            # At least one task is present here because the loop has work left.
            done_tasks, pending_tasks = await asyncio.wait(
                pending_tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done_tasks:
                # task.result() also re-raises unexpected coroutine failures.
                url, discovered_links = task.result()
                if discovered_links is None:
                    self.failed_urls.add(url)
                    continue

                self.fetched_urls.append(url)
                for link in discovered_links:
                    if link not in self.discovered_urls:
                        self.discovered_urls.add(link)
                        self.urls_to_crawl.append(link)

        return self.fetched_urls.copy()


async def main() -> None:
    """Run the async crawler from the command line."""
    crawler = AsyncWebCrawler(HOME_URL)
    pages = await crawler.run()
    print("Asyncio crawl:", sorted(pages))


if __name__ == "__main__":
    asyncio.run(main())
