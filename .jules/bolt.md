## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-11 - Parallelizing PocketBase Operations
**Learning:** The PocketBase Python SDK utilizes `httpx.Client` internally and is completely thread-safe. This allows I/O blocking loops like N+1 queries or deletions to be safely run through `concurrent.futures.ThreadPoolExecutor`.
**Action:** When identifying sequential loops performing PocketBase database requests, refactor them using threaded maps to maximize throughput, while avoiding mutative state within the worker function to prevent race conditions.
