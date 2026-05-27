"""Lesson: cancel pending tasks and wait for their cleanup."""

import asyncio


async def fetch_page(name: str, delay_seconds: float) -> str:
    """Return a page name after a simulated network delay."""
    await asyncio.sleep(delay_seconds)
    return name


async def cancel_after_first_completion(
    request_delays: dict[str, float],
) -> tuple[set[str], set[str]]:
    """Keep the first completed results and cancel all slower requests."""
    if not request_delays:
        return set(), set()

    tasks = {
        asyncio.create_task(fetch_page(name, delay_seconds)): name
        for name, delay_seconds in request_delays.items()
    }

    done_tasks, pending_tasks = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )
    completed_names = {task.result() for task in done_tasks}

    tasks_to_cancel = list(pending_tasks)
    for task in tasks_to_cancel:
        task.cancel()

    cancellation_results = await asyncio.gather(
        *tasks_to_cancel,
        return_exceptions=True,
    )
    cancelled_names = {
        tasks[task]
        for task, result in zip(tasks_to_cancel, cancellation_results)
        if isinstance(result, asyncio.CancelledError)
    }
    return completed_names, cancelled_names


async def main() -> None:
    """Show that slow requests are explicitly cancelled and collected."""
    completed, cancelled = await cancel_after_first_completion(
        {"fast-page": 0.01, "slow-page-a": 0.10, "slow-page-b": 0.12}
    )
    print("Completed:", sorted(completed))
    print("Cancelled:", sorted(cancelled))


if __name__ == "__main__":
    asyncio.run(main())
