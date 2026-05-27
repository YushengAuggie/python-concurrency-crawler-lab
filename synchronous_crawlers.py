"""Blocking crawler examples: sequential execution and thread-pool concurrency."""

from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import threading

from shared import HOME_URL, get_html_content, get_links_on_page


class SequentialWebCrawler:
    """Crawl pages one at a time in breadth-first order."""

    def __init__(self, starting_url: str):
        # Mark each URL as discovered when it is queued to prevent duplicates.
        self.discovered_urls = {starting_url}
        self.urls_to_crawl = deque([starting_url])
        self.fetched_urls: list[str] = []
        self.failed_urls: set[str] = set()

    def crawl_page(self, url: str) -> None:
        """Fetch one page and queue links that have not been discovered before."""
        try:
            html_content = get_html_content(url)
        except ConnectionError:
            self.failed_urls.add(url)
            return

        self.fetched_urls.append(url)
        for link in get_links_on_page(html_content, url):
            if link not in self.discovered_urls:
                self.discovered_urls.add(link)
                self.urls_to_crawl.append(link)

    def run(self) -> list[str]:
        """Crawl until every discovered page has been handled."""
        while self.urls_to_crawl:
            current_url = self.urls_to_crawl.popleft()
            self.crawl_page(current_url)

        return self.fetched_urls.copy()


class ThreadPoolWebCrawler:
    """Crawl blocking page requests concurrently by using worker threads."""

    def __init__(self, starting_url: str, max_workers: int = 20):
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        self.discovered_urls = {starting_url}
        self.urls_to_crawl = deque([starting_url])
        self.state_lock = threading.Lock()
        self.pending_futures: set[Future[None]] = set()
        self.fetched_urls: list[str] = []
        self.failed_urls: set[str] = set()
        self.max_workers = max_workers

    def crawl_page(self, url: str) -> None:
        """Fetch one page, then atomically deduplicate and queue its links."""
        try:
            html_content = get_html_content(url)
        except ConnectionError:
            with self.state_lock:
                self.failed_urls.add(url)
            return

        discovered_links = get_links_on_page(html_content, url)
        with self.state_lock:
            self.fetched_urls.append(url)
            # The check-and-enqueue sequence must not race with another thread.
            for link in discovered_links:
                if link not in self.discovered_urls:
                    self.discovered_urls.add(link)
                    self.urls_to_crawl.append(link)

    def run(self) -> list[str]:
        """Keep a bounded set of page requests in flight until crawling ends."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as thread_pool:
            while True:
                with self.state_lock:
                    available_worker_slots = (
                        self.max_workers - len(self.pending_futures)
                    )
                    pages_to_submit = min(
                        available_worker_slots, len(self.urls_to_crawl)
                    )

                    for _ in range(pages_to_submit):
                        url = self.urls_to_crawl.popleft()
                        future = thread_pool.submit(self.crawl_page, url)
                        self.pending_futures.add(future)

                    # In-flight pages can discover more URLs, so both states
                    # must be empty before it is safe to terminate the crawl.
                    if not self.urls_to_crawl and not self.pending_futures:
                        break

                # Wait for real progress rather than polling worker completion.
                done_futures, pending_futures = wait(
                    self.pending_futures,
                    return_when=FIRST_COMPLETED,
                )

                for future in done_futures:
                    # result() re-raises unexpected failures from worker threads.
                    future.result()

                self.pending_futures = pending_futures

        return self.fetched_urls.copy()


if __name__ == "__main__":
    sequential_pages = SequentialWebCrawler(HOME_URL).run()
    thread_pool_pages = ThreadPoolWebCrawler(HOME_URL).run()

    print("Sequential crawl order:", sequential_pages)
    print("Thread-pool fetched pages:", sorted(thread_pool_pages))
