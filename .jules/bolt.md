## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-07-03 - Concurrent database API calls in ThreadPoolExecutor
**Learning:** Sequential loops that perform I/O bound DB operations (e.g. `delete()`) over many records cause serious performance bottlenecks.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` with `as_completed()` to parallelize these calls while safely collecting stats and errors sequentially in the main thread.
