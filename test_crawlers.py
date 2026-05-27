"""Behavior tests shared by each crawler implementation."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from async_crawler import AsyncWebCrawler
from shared import EXAMPLE_WEBSITE, HOME_URL, get_html_content, get_links_on_page
from synchronous_crawlers import SequentialWebCrawler, ThreadPoolWebCrawler


class LinkParsingTests(unittest.TestCase):
    """Verify URL normalization and filtering behavior."""

    def test_home_page_keeps_only_normalized_same_site_links(self) -> None:
        links = get_links_on_page(get_html_content(HOME_URL), HOME_URL)

        self.assertEqual(
            links,
            [
                "https://learn.example.com/tutorial",
                "https://learn.example.com/reference",
            ],
        )


class CrawlerTests(unittest.TestCase):
    """Verify every crawler reaches the same pages without duplicates."""

    def setUp(self) -> None:
        self.expected_pages = set(EXAMPLE_WEBSITE)

    def test_sequential_crawler(self) -> None:
        pages = SequentialWebCrawler(HOME_URL).run()
        self.assertEqual(set(pages), self.expected_pages)
        self.assertEqual(
            pages,
            [
                HOME_URL,
                "https://learn.example.com/tutorial",
                "https://learn.example.com/reference",
                "https://learn.example.com/examples/basic",
                "https://learn.example.com/examples/concurrent",
            ],
        )

    def test_thread_pool_crawler(self) -> None:
        pages = ThreadPoolWebCrawler(HOME_URL, max_workers=2).run()
        self.assertEqual(set(pages), self.expected_pages)

    def test_async_crawler(self) -> None:
        pages = asyncio.run(
            AsyncWebCrawler(HOME_URL, max_concurrency=2).run()
        )
        self.assertEqual(set(pages), self.expected_pages)

    def test_missing_start_page_is_recorded_as_failed(self) -> None:
        missing_url = "https://learn.example.com/missing"
        for crawler in (
            SequentialWebCrawler(missing_url),
            ThreadPoolWebCrawler(missing_url, max_workers=2),
        ):
            self.assertEqual(crawler.run(), [])
            self.assertEqual(crawler.failed_urls, {missing_url})

        async_crawler = AsyncWebCrawler(missing_url, max_concurrency=2)
        self.assertEqual(asyncio.run(async_crawler.run()), [])
        self.assertEqual(async_crawler.failed_urls, {missing_url})

    def test_invalid_concurrency_limits_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ThreadPoolWebCrawler(HOME_URL, max_workers=0)
        with self.assertRaises(ValueError):
            AsyncWebCrawler(HOME_URL, max_concurrency=0)

    def test_async_unexpected_failure_is_propagated(self) -> None:
        with patch(
            "async_crawler.get_html_content_async",
            new=AsyncMock(side_effect=RuntimeError("unexpected failure")),
        ):
            with self.assertRaises(RuntimeError):
                asyncio.run(AsyncWebCrawler(HOME_URL).run())

    def test_thread_pool_unexpected_failure_is_propagated(self) -> None:
        with patch(
            "synchronous_crawlers.get_html_content",
            side_effect=RuntimeError("unexpected failure"),
        ):
            with self.assertRaises(RuntimeError):
                ThreadPoolWebCrawler(HOME_URL).run()



if __name__ == "__main__":
    unittest.main()
