## 2026-04-06 - N+1 Query in Discovery Loop
**Learning:** Sequential queries in inner loops are a common performance anti-pattern.
**Action:** Use get_full_list with specific fields to prefetch and dictionary-cache database records before looping.
## 2026-05-31 - Thread-Safe PocketBase Deletions
**Learning:** PocketBase Python SDK uses `httpx.Client` internally, which is thread-safe. When the `/api/batch` endpoint is unavailable, parallelizing sequential database deletions using `concurrent.futures.ThreadPoolExecutor` safely eliminates network latency overhead.
**Action:** Always parallelize independent I/O-bound PocketBase operations (like bulk deletes or updates) via threads when batch endpoints are missing to massively speed up background tasks.
