"""Shared offline website and link utilities for crawler examples."""

import asyncio
from html.parser import HTMLParser
import time
from urllib.parse import urldefrag, urljoin, urlparse


HOME_URL = "https://learn.example.com/"

# This website deliberately contains cycles, duplicates, fragments, and
# non-crawlable links so each crawler has realistic filtering work to do.
EXAMPLE_WEBSITE = {
    HOME_URL: """
        <html><body>
            <h1>Learn Concurrent Crawling</h1>
            <a href="/tutorial">Tutorial</a>
            <a href="/reference">Reference</a>
            <a href="/tutorial#threads">Duplicate tutorial fragment</a>
            <a href="mailto:teacher@example.com">Email the teacher</a>
            <a href="https://news.example.net/story">External news</a>
        </body></html>
    """,
    "https://learn.example.com/tutorial": """
        <html><body>
            <a href="/reference">Reference</a>
            <a href="/examples/basic">Basic example</a>
            <a href="/">Back home</a>
        </body></html>
    """,
    "https://learn.example.com/reference": """
        <html><body>
            <a href="/examples/basic#result">Basic example result</a>
            <a href="/examples/concurrent">Concurrent example</a>
            <a href="javascript:void(0)">Not a page</a>
        </body></html>
    """,
    "https://learn.example.com/examples/basic": """
        <html><body>
            <a href="/examples/concurrent">Try concurrency next</a>
        </body></html>
    """,
    "https://learn.example.com/examples/concurrent": """
        <html><body>
            <a href="/tutorial">Review the tutorial</a>
        </body></html>
    """,
}

PAGE_DOWNLOAD_DELAYS = {
    HOME_URL: 0.04,
    "https://learn.example.com/tutorial": 0.08,
    "https://learn.example.com/reference": 0.05,
    "https://learn.example.com/examples/basic": 0.03,
    "https://learn.example.com/examples/concurrent": 0.06,
}


def _read_example_page(url: str) -> str:
    """Validate a URL and return its HTML from the offline example website."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ConnectionError(f"Unsupported URL scheme: {url}")

    try:
        return EXAMPLE_WEBSITE[url]
    except KeyError as error:
        raise ConnectionError(f"Page not found: {url}") from error


def get_html_content(url: str) -> str:
    """Fetch one page through a blocking API that simulates network latency."""
    time.sleep(PAGE_DOWNLOAD_DELAYS.get(url, 0.02))
    return _read_example_page(url)


async def get_html_content_async(url: str) -> str:
    """Fetch one page without blocking the asyncio event loop while waiting."""
    await asyncio.sleep(PAGE_DOWNLOAD_DELAYS.get(url, 0.02))
    return _read_example_page(url)


class _LinkParser(HTMLParser):
    """Collect raw hyperlink targets from anchor elements in an HTML page."""

    def __init__(self) -> None:
        super().__init__()
        self.raw_links: list[str] = []

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "a":
            return

        for attribute_name, attribute_value in attributes:
            if attribute_name.lower() == "href" and attribute_value:
                self.raw_links.append(attribute_value)
                return


def get_links_on_page(html_content: str, page_url: str) -> list[str]:
    """Extract normalized, same-site HTTP links from a downloaded HTML page."""
    parser = _LinkParser()
    parser.feed(html_content)

    site_host = urlparse(page_url).netloc
    normalized_links: list[str] = []
    seen_links: set[str] = set()

    for raw_link in parser.raw_links:
        absolute_link = urljoin(page_url, raw_link)
        normalized_link, _fragment = urldefrag(absolute_link)
        parsed_link = urlparse(normalized_link)

        # Keep the crawl on one website and exclude mail, scripts, and similar URLs.
        if parsed_link.scheme not in {"http", "https"}:
            continue
        if parsed_link.netloc != site_host:
            continue

        if normalized_link not in seen_links:
            seen_links.add(normalized_link)
            normalized_links.append(normalized_link)

    return normalized_links
