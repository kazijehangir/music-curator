## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-04 - Parallelizing PocketBase Operations
**Learning:** PocketBase Python SDK operations (like `delete()` or `update()`) can be safely parallelized because the underlying `httpx.Client` is thread-safe.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize independent database operations to avoid sequential bottlenecking, especially for bulk cleanups or updates.
