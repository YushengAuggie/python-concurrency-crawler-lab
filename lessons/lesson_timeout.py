"""Lesson: protect an asynchronous fetch with a timeout."""

import asyncio

from shared import HOME_URL, get_html_content_async


async def fetch_with_timeout(url: str, timeout_seconds: float) -> str | None:
    """Return page HTML, or None when the request exceeds its time budget."""
    try:
        return await asyncio.wait_for(
            get_html_content_async(url),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        return None


async def main() -> None:
    """Show one timed-out request and one successful request."""
    timed_out_html = await fetch_with_timeout(HOME_URL, timeout_seconds=0.01)
    successful_html = await fetch_with_timeout(HOME_URL, timeout_seconds=0.10)

    print("Short timeout failed:", timed_out_html is None)
    print("Long timeout succeeded:", successful_html is not None)


if __name__ == "__main__":
    asyncio.run(main())
