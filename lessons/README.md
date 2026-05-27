# Progressive Asyncio Lessons

[English](README.md) | [简体中文](README.zh-CN.md) | [Back to project home](../README.md)

These small lessons continue after the core crawler comparison. Each lesson is independently runnable, changes one idea at a time, and ends with a self-check.

## Suggested Order

| Lesson | Runnable example | New idea |
| --- | --- | --- |
| 1 | `lesson_timeout.py` | Stop waiting after a time budget |
| 2 | `lesson_retry.py` | Retry temporary failures with bounded backoff |
| 3 | `lesson_semaphore.py` | Bound active async requests |
| 4 | `lesson_cancellation.py` | Cancel and collect unfinished tasks |

Run every lesson from the project root:

```bash
python3 -m lessons.lesson_timeout
python3 -m lessons.lesson_retry
python3 -m lessons.lesson_semaphore
python3 -m lessons.lesson_cancellation
python3 -m unittest -v
```

## Lesson 1: Timeout

**Goal:** Understand why an async request needs a time budget even though it does not block the event loop.

Open `lessons/lesson_timeout.py` and find:

```python
return await asyncio.wait_for(
    get_html_content_async(url),
    timeout=timeout_seconds,
)
```

`await` lets other tasks run; it does not guarantee this task will finish soon. `asyncio.wait_for()` cancels the inner wait when its timeout expires and raises `asyncio.TimeoutError` on Python 3.10, which the lesson converts to `None`. The function waits for cancellation cleanup to finish, so actual elapsed time can exceed the nominal timeout.

### Try It

1. Run `python3 -m lessons.lesson_timeout`.
2. Change the short timeout from `0.01` to `0.10`.
3. Run it again and explain why both requests now succeed.

### Self-Check

- Can I explain the difference between non-blocking waiting and bounded waiting?
- Can I point to where `asyncio.TimeoutError` is handled?
- Can I explain why timeout values should come from application needs, not guesses?

You are ready to continue when you can predict the output before running the script.

## Lesson 2: Retry With Backoff

**Goal:** Recover from temporary failures without retrying forever or immediately flooding a service.

`lessons/lesson_retry.py` deliberately fails twice, then succeeds:

```python
delay_seconds = base_delay_seconds * (2 ** (attempt_number - 1))
await asyncio.sleep(delay_seconds)
```

The retry budget is bounded by `max_attempts`; the increasing delay is exponential backoff.

### Try It

1. Run `python3 -m lessons.lesson_retry`; it should succeed on attempt 3.
2. Set `failures_before_success=3` while leaving `max_attempts=3`.
3. Observe that the final temporary failure is raised instead of looping forever.

### Self-Check

- Which failures are reasonable to retry, and which should fail immediately?
- Why must the number of attempts be limited?
- Why does backoff help when a remote service is overloaded?

You are ready to continue when you can state both the retry condition and the stopping condition.

## Lesson 3: Semaphore

**Goal:** Distinguish the number of scheduled tasks from the number of active requests.

`lessons/lesson_semaphore.py` schedules six tasks but allows only two inside the simulated request at a time:

```python
async with semaphore:
    await asyncio.sleep(0.02)
```

An `asyncio.Semaphore` represents a limited number of permits. Tasks that cannot acquire one pause until another task releases its permit.

### Try It

1. Run `python3 -m lessons.lesson_semaphore`.
2. Change `limit=2` to `limit=1` and then `limit=4`.
3. Observe how `Maximum active requests` changes while `Tasks scheduled` remains six.

### Self-Check

- Can I explain why creating many tasks does not require allowing all requests to be active?
- What resource might a semaphore protect in a real crawler?
- How is this related to, but different from, limiting the total number of pages crawled?

You are ready to continue when you can distinguish active-request limits from total crawl-size limits.

## Lesson 4: Cancellation

**Goal:** Stop work that is no longer needed and still observe its completion state.

`lessons/lesson_cancellation.py` keeps the fastest result and cancels slower tasks:

```python
for task in pending_tasks:
    task.cancel()

cancellation_results = await asyncio.gather(
    *pending_tasks,
    return_exceptions=True,
)
```

Calling `cancel()` requests cancellation. Awaiting or gathering cancelled tasks allows their cancellation to finish cleanly and makes the outcome observable.

### Try It

1. Run `python3 -m lessons.lesson_cancellation`.
2. Give both slow requests a delay of `0.0`.
3. Observe that more than one task may already be complete when the event loop checks results.

### Self-Check

- Why is calling `cancel()` alone not the complete cleanup story?
- Where would cancellation matter in a web crawler or API client?
- What cleanup would belong in a `finally` block if a task held a resource?

You have completed the core progression when you can explain timeout, retry, active concurrency limits, and cancellation without mixing their responsibilities.

## Next Build Exercise: Bound Crawl Growth

The base crawler limits active requests but not the total frontier. As a final exercise, add `max_pages` to `AsyncWebCrawler`:

1. Stop enqueuing new links after `max_pages` unique URLs have been discovered.
2. Preserve the existing `max_concurrency` behavior.
3. Add a test that crawls with `max_pages=3` and asserts only three pages are fetched.
4. Explain why `Semaphore` and `max_pages` solve different resource problems.

This exercise deliberately remains for the learner: it connects the lessons to the crawler without hiding the design decision in finished code.
