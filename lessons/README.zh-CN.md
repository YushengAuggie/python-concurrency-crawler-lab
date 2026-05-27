# Asyncio 进阶课程 | Progressive Asyncio Lessons

[English](README.md) | [简体中文](README.zh-CN.md) | [返回项目首页](../README.zh-CN.md)

这些小课程承接核心 crawler 对比部分。每一课都可以独立运行，只引入一个新概念，并在最后提供自查环节。

## 建议顺序 | Suggested Order

| 课程 | 可运行例子 | 新概念 |
| --- | --- | --- |
| 1 | `lesson_timeout.py` | 超过时间预算后停止等待 |
| 2 | `lesson_retry.py` | 用受限退避处理临时失败 |
| 3 | `lesson_semaphore.py` | 限制活跃 async 请求数量 |
| 4 | `lesson_cancellation.py` | 取消并收集未完成任务 |

请在项目根目录运行：

```bash
python3 -m lessons.lesson_timeout
python3 -m lessons.lesson_retry
python3 -m lessons.lesson_semaphore
python3 -m lessons.lesson_cancellation
python3 -m unittest -v
```

## Lesson 1：超时 | Timeout

**目标：** 理解异步请求虽然不会阻塞 event loop，但仍然需要时间预算。

打开 `lessons/lesson_timeout.py`，找到：

```python
return await asyncio.wait_for(
    get_html_content_async(url),
    timeout=timeout_seconds,
)
```

`await` 表示等待期间可以运行其他 tasks；它不保证当前 task 会及时结束。在 Python 3.10 中，`asyncio.wait_for()` 会在超时时取消内部等待并抛出 `asyncio.TimeoutError`，本例将它转换为 `None`。该函数会等待取消清理完成，因此实际经过时间可能超过名义 timeout。

### 动手操作 | Try It

1. 运行 `python3 -m lessons.lesson_timeout`。
2. 将短 timeout 从 `0.01` 改为 `0.10`。
3. 再次运行，并解释为什么这时两个请求都成功。

### 自查 | Self-Check

- 我能否解释 non-blocking wait 和 bounded wait 的区别？
- 我能否指出 `asyncio.TimeoutError` 在哪里被处理？
- 我能否解释为什么 timeout 应根据应用需求设定，而不是随意猜测？

当你能够在运行脚本之前预测输出，就可以进入下一课。

## Lesson 2：退避重试 | Retry With Backoff

**目标：** 对临时失败进行恢复，同时避免无限重试或立刻加重服务压力。

`lessons/lesson_retry.py` 会故意失败两次，然后成功：

```python
delay_seconds = base_delay_seconds * (2 ** (attempt_number - 1))
await asyncio.sleep(delay_seconds)
```

`max_attempts` 限定重试预算；逐渐增加的等待时间称为 exponential backoff（指数退避）。

### 动手操作 | Try It

1. 运行 `python3 -m lessons.lesson_retry`；它应在第 3 次尝试成功。
2. 将 `failures_before_success=3`，保留 `max_attempts=3`。
3. 观察最后一次临时失败会被抛出，而不是无限循环。

### 自查 | Self-Check

- 哪些失败适合 retry，哪些失败应该立即终止？
- 为什么必须限制 attempt 数量？
- 服务过载时，backoff 为什么有帮助？

当你能说清“什么时候重试”与“什么时候停止”，就可以继续。

## Lesson 3：信号量 | Semaphore

**目标：** 区分已调度 task 数量与正在活跃执行的请求数量。

`lessons/lesson_semaphore.py` 会安排六个 tasks，但一次最多允许两个进入模拟请求：

```python
async with semaphore:
    await asyncio.sleep(0.02)
```

`asyncio.Semaphore` 表示有限数量的 permits（许可）。拿不到许可的 task 会暂停，等待其他 task 释放许可。

### 动手操作 | Try It

1. 运行 `python3 -m lessons.lesson_semaphore`。
2. 将 `limit=2` 分别改为 `limit=1` 与 `limit=4`。
3. 观察 `Maximum active requests` 如何变化，而 `Tasks scheduled` 仍为六个。

### 自查 | Self-Check

- 我能否解释为什么创建许多 tasks 不等于允许所有请求同时活跃？
- 在真实 crawler 中，semaphore 可以保护什么资源？
- 限制活跃请求与限制总抓取页面数量有什么区别？

当你能清楚区分 active-request limit 与 total crawl-size limit，就可以进入下一课。

## Lesson 4：取消任务 | Cancellation

**目标：** 停止已经不再需要的工作，并正确观察其结束状态。

`lessons/lesson_cancellation.py` 保留最快结果，并取消更慢的 tasks：

```python
for task in pending_tasks:
    task.cancel()

cancellation_results = await asyncio.gather(
    *pending_tasks,
    return_exceptions=True,
)
```

调用 `cancel()` 是请求取消。继续 `await` 或 `gather` 已取消任务，能够让取消流程完整结束，并使结果可观察。

### 动手操作 | Try It

1. 运行 `python3 -m lessons.lesson_cancellation`。
2. 将两个慢请求的 delay 都改为 `0.0`。
3. 观察 event loop 检查结果时，可能已有多个任务完成。

### 自查 | Self-Check

- 为什么只调用 `cancel()` 还不是完整的清理过程？
- Cancellation 在 crawler 或 API client 中什么时候重要？
- 如果 task 持有资源，哪些清理应放在 `finally` 中？

当你能分别解释 timeout、retry、活跃并发上限和 cancellation，而不会混淆它们的职责，就完成了核心进阶路线。

## 最后实践：限制爬虫增长 | Bound Crawl Growth

基础 crawler 限制了活跃请求数量，但没有限制总 frontier。作为最后的动手练习，请为 `AsyncWebCrawler` 增加 `max_pages`：

1. 当发现过的唯一 URL 达到 `max_pages` 后，停止加入新链接。
2. 保留已有的 `max_concurrency` 行为。
3. 添加测试：使用 `max_pages=3` 运行后，断言只抓取三个页面。
4. 解释为什么 `Semaphore` 与 `max_pages` 解决的是不同资源问题。

这个练习刻意留给学习者完成：它将课程概念连接回 crawler，同时保留真正需要思考的设计步骤。
