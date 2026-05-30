## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.


## 2026-05-30 - Parallelizing PocketBase Operations
**Learning:** The PocketBase Python SDK uses `httpx.Client` internally, which is thread-safe, making it safe to parallelize API operations like `.update()` and `.delete()`.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize individual sequential PocketBase API calls to avoid N+1 network bottlenecks.
