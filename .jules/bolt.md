## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.

## 2026-06-03 - PocketBase Python SDK Thread Safety
**Learning:** The PocketBase Python SDK internally utilizes `httpx.Client`, which is thread-safe. This allows sequential database operations like `.delete()` or `.update()` to be parallelized directly.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` to parallelize sequential N+1 PocketBase mutations where the `/api/batch` endpoint is unavailable.
